#!/bin/bash
set -e

echo "⚡ FAST AWS DEPLOYMENT - Watcher"
echo "=================================="
echo ""

# Load environment
if [ -f ../.env ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
fi

# Validate
if [ -z "$LLM_API_KEY" ]; then
    echo "❌ LLM_API_KEY not found in .env"
    exit 1
fi

export AWS_REGION=${AWS_REGION:-us-east-1}
export AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)

echo "📍 Region: $AWS_REGION"
echo "🔑 API Key: ${LLM_API_KEY:0:10}..."
echo ""

# Install CDK deps
echo "📦 Installing CDK..."
cd cdk
npm install --silent

# Bootstrap
echo "🔧 Bootstrapping CDK..."
npx cdk bootstrap aws://$AWS_ACCOUNT/$AWS_REGION --require-approval never 2>/dev/null || true

# Deploy infrastructure
echo "🏗️  Deploying infrastructure (10-15 min)..."
npx cdk deploy --require-approval never --outputs-file outputs.json

# Extract outputs
BACKEND_REPO=$(cat outputs.json | grep -o '"WatcherStack.BackendRepoUri": "[^"]*"' | cut -d'"' -f4)
FRONTEND_REPO=$(cat outputs.json | grep -o '"WatcherStack.FrontendRepoUri": "[^"]*"' | cut -d'"' -f4)
CLOUDFRONT_URL=$(cat outputs.json | grep -o '"WatcherStack.CloudFrontURL": "[^"]*"' | cut -d'"' -f4)
ALB_DNS=$(cat outputs.json | grep -o '"WatcherStack.LoadBalancerDNS": "[^"]*"' | cut -d'"' -f4)

echo ""
echo "✅ Infrastructure deployed!"
echo "Backend: $BACKEND_REPO"
echo "Frontend: $FRONTEND_REPO"
echo ""

# Login to ECR
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com

# Build and push backend
echo "🐳 Building backend (3-5 min)..."
cd ../../backend
docker build -t watcher-backend -q .
docker tag watcher-backend:latest $BACKEND_REPO:latest
echo "📤 Pushing backend..."
docker push $BACKEND_REPO:latest -q

# Build and push frontend  
echo "🐳 Building frontend (2-3 min)..."
cd ../frontend
docker build -t watcher-frontend --build-arg REACT_APP_API_URL=http://$ALB_DNS -q .
docker tag watcher-frontend:latest $FRONTEND_REPO:latest
echo "📤 Pushing frontend..."
docker push $FRONTEND_REPO:latest -q

echo ""
echo "✅ Images pushed!"
echo ""

# Update services
echo "🔄 Deploying to ECS..."
CLUSTER=$(aws ecs list-clusters --region $AWS_REGION --query 'clusterArns[?contains(@, `WatcherStack`)]' --output text | cut -d'/' -f2)

aws ecs update-service --cluster $CLUSTER --service WatcherStack-BackendService --force-new-deployment --region $AWS_REGION --no-cli-pager >/dev/null 2>&1 &
aws ecs update-service --cluster $CLUSTER --service WatcherStack-FrontendService --force-new-deployment --region $AWS_REGION --no-cli-pager >/dev/null 2>&1 &
aws ecs update-service --cluster $CLUSTER --service WatcherStack-CeleryService --force-new-deployment --region $AWS_REGION --no-cli-pager >/dev/null 2>&1 &
aws ecs update-service --cluster $CLUSTER --service WatcherStack-BeatService --force-new-deployment --region $AWS_REGION --no-cli-pager >/dev/null 2>&1 &

wait

echo "⏳ Waiting for services (2 min)..."
sleep 120

# Get task info for migrations
echo "🗄️  Running migrations..."
BACKEND_SERVICE=$(aws ecs list-services --cluster $CLUSTER --region $AWS_REGION --query 'serviceArns[?contains(@, `BackendService`)]' --output text | cut -d'/' -f3)
SERVICE_INFO=$(aws ecs describe-services --cluster $CLUSTER --services $BACKEND_SERVICE --region $AWS_REGION)
TASK_DEF=$(echo $SERVICE_INFO | grep -o '"taskDefinition": "[^"]*"' | head -1 | cut -d'"' -f4)
SUBNET=$(echo $SERVICE_INFO | grep -o 'subnet-[a-z0-9]*' | head -1)
SG=$(echo $SERVICE_INFO | grep -o 'sg-[a-z0-9]*' | head -1)

# Run migrations
echo "Running migrate..."
TASK=$(aws ecs run-task \
    --cluster $CLUSTER \
    --task-definition $TASK_DEF \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNET],securityGroups=[$SG],assignPublicIp=DISABLED}" \
    --overrides '{"containerOverrides":[{"name":"backend","command":["python","manage.py","migrate"]}]}' \
    --region $AWS_REGION \
    --query 'tasks[0].taskArn' \
    --output text)
aws ecs wait tasks-stopped --cluster $CLUSTER --tasks $TASK --region $AWS_REGION

# Populate data
echo "📊 Populating public haunts..."
TASK=$(aws ecs run-task \
    --cluster $CLUSTER \
    --task-definition $TASK_DEF \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNET],securityGroups=[$SG],assignPublicIp=DISABLED}" \
    --overrides '{"containerOverrides":[{"name":"backend","command":["python","manage.py","populate_public_haunts"]}]}' \
    --region $AWS_REGION \
    --query 'tasks[0].taskArn' \
    --output text)
aws ecs wait tasks-stopped --cluster $CLUSTER --tasks $TASK --region $AWS_REGION

echo "👤 Creating demo user..."
TASK=$(aws ecs run-task \
    --cluster $CLUSTER \
    --task-definition $TASK_DEF \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNET],securityGroups=[$SG],assignPublicIp=DISABLED}" \
    --overrides '{"containerOverrides":[{"name":"backend","command":["python","manage.py","populate_demo_data"]}]}' \
    --region $AWS_REGION \
    --query 'tasks[0].taskArn' \
    --output text)
aws ecs wait tasks-stopped --cluster $CLUSTER --tasks $TASK --region $AWS_REGION

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "=================================="
echo ""
echo "🌐 CloudFront URL: $CLOUDFRONT_URL"
echo "🔗 ALB URL: http://$ALB_DNS"
echo ""
echo "🔑 Demo Login:"
echo "   Email: demo@watcher.local"
echo "   Password: demo123"
echo ""
echo "⚠️  Note: CloudFront may take 10-15 min to fully propagate"
echo "   Use ALB URL for immediate access"
echo ""
