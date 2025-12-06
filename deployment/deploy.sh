#!/bin/bash
set -e

echo "🚀 Watcher AWS Deployment"
echo "========================="
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
echo "🔑 Account: $AWS_ACCOUNT"
echo ""

# Step 1: Deploy infrastructure with services at 0
echo "🏗️  Deploying infrastructure..."
cd cdk
npm install --silent
npx cdk bootstrap aws://$AWS_ACCOUNT/$AWS_REGION --require-approval never 2>/dev/null || true
npx cdk deploy --require-approval never --outputs-file outputs.json

# Extract outputs
BACKEND_REPO=$(cat outputs.json | grep -o '"BackendRepoUri": "[^"]*"' | cut -d'"' -f4)
FRONTEND_REPO=$(cat outputs.json | grep -o '"FrontendRepoUri": "[^"]*"' | cut -d'"' -f4)
CLOUDFRONT_URL=$(cat outputs.json | grep -o '"CloudFrontURL": "[^"]*"' | cut -d'"' -f4)
ALB_DNS=$(cat outputs.json | grep -o '"LoadBalancerDNS": "[^"]*"' | cut -d'"' -f4)

echo "✅ Infrastructure deployed"
echo ""

# Step 2: Build and push images
echo "🐳 Building and pushing images..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com

cd ../../backend
docker build -t watcher-backend .
docker tag watcher-backend:latest $BACKEND_REPO:latest
docker push $BACKEND_REPO:latest

cd ../frontend
# Use relative URL so frontend uses same origin (CloudFront HTTPS)
docker build -t watcher-frontend --build-arg REACT_APP_API_URL="" .
docker tag watcher-frontend:latest $FRONTEND_REPO:latest
docker push $FRONTEND_REPO:latest

echo "✅ Images pushed"
echo ""

# Step 3: Scale up services
echo "🔄 Scaling up ECS services..."
CLUSTER=$(aws ecs list-clusters --region $AWS_REGION --query 'clusterArns[?contains(@, `WatcherStack`)]' --output text | cut -d'/' -f2)

# Get actual service names
BACKEND_SVC=$(aws ecs list-services --cluster $CLUSTER --region $AWS_REGION --query 'serviceArns[?contains(@, `BackendService`)]' --output text | cut -d'/' -f3)
FRONTEND_SVC=$(aws ecs list-services --cluster $CLUSTER --region $AWS_REGION --query 'serviceArns[?contains(@, `FrontendService`)]' --output text | cut -d'/' -f3)
CELERY_SVC=$(aws ecs list-services --cluster $CLUSTER --region $AWS_REGION --query 'serviceArns[?contains(@, `CeleryService`)]' --output text | cut -d'/' -f3)
BEAT_SVC=$(aws ecs list-services --cluster $CLUSTER --region $AWS_REGION --query 'serviceArns[?contains(@, `BeatService`)]' --output text | cut -d'/' -f3)

aws ecs update-service --cluster $CLUSTER --service $BACKEND_SVC --desired-count 1 --region $AWS_REGION --no-cli-pager >/dev/null
aws ecs update-service --cluster $CLUSTER --service $FRONTEND_SVC --desired-count 1 --region $AWS_REGION --no-cli-pager >/dev/null
aws ecs update-service --cluster $CLUSTER --service $CELERY_SVC --desired-count 1 --region $AWS_REGION --no-cli-pager >/dev/null
aws ecs update-service --cluster $CLUSTER --service $BEAT_SVC --desired-count 1 --region $AWS_REGION --no-cli-pager >/dev/null

echo "⏳ Waiting for services to stabilize (3-5 min)..."
aws ecs wait services-stable --cluster $CLUSTER --services $BACKEND_SVC --region $AWS_REGION
aws ecs wait services-stable --cluster $CLUSTER --services $FRONTEND_SVC --region $AWS_REGION

echo "✅ Services running"
echo ""

# Step 4: Run migrations
echo "🗄️  Running migrations..."
SERVICE_INFO=$(aws ecs describe-services --cluster $CLUSTER --services $BACKEND_SVC --region $AWS_REGION)
TASK_DEF=$(echo "$SERVICE_INFO" | grep -o '"taskDefinition": "[^"]*"' | head -1 | cut -d'"' -f4)
SUBNET=$(echo "$SERVICE_INFO" | grep -o 'subnet-[a-z0-9]*' | head -1)
SG=$(echo "$SERVICE_INFO" | grep -o 'sg-[a-z0-9]*' | head -1)

run_task() {
    local command=$1
    local description=$2
    echo "$description"
    TASK=$(aws ecs run-task \
        --cluster $CLUSTER \
        --task-definition $TASK_DEF \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNET],securityGroups=[$SG],assignPublicIp=DISABLED}" \
        --overrides "{\"containerOverrides\":[{\"name\":\"backend\",\"command\":$command}]}" \
        --region $AWS_REGION \
        --query 'tasks[0].taskArn' \
        --output text)
    aws ecs wait tasks-stopped --cluster $CLUSTER --tasks $TASK --region $AWS_REGION
}

run_task '["python","manage.py","migrate"]' "Running migrations..."
run_task '["python","manage.py","populate_public_haunts"]' "Populating public haunts..."
run_task '["python","manage.py","populate_demo_data"]' "Creating demo user..."

echo "✅ Database setup complete"
echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================="
echo ""
echo "🌐 CloudFront: $CLOUDFRONT_URL"
echo "🔗 ALB: http://$ALB_DNS"
echo ""
echo "🔑 Demo Login:"
echo "   Email: demo@watcher.local"
echo "   Password: demo123"
echo ""
echo "⚠️  CloudFront may take 10-15 min to propagate"
echo "   Use ALB URL for immediate access"
echo ""
