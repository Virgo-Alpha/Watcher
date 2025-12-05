#!/bin/bash
set -e

echo "🚀 Starting Watcher AWS Deployment..."
echo "⏱️  Estimated time: 20-30 minutes"
echo ""

# Load environment variables
if [ -f ../.env ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
fi

# Validate LLM_API_KEY
if [ -z "$LLM_API_KEY" ]; then
    echo "❌ LLM_API_KEY not found in .env file"
    echo "Please add your Google Gemini API key to .env"
    exit 1
fi

# Get AWS account and region
export AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=${AWS_REGION:-us-east-1}

echo "📍 Deploying to Account: $AWS_ACCOUNT, Region: $AWS_REGION"
echo "🔑 Using API Key: ${LLM_API_KEY:0:10}..."
echo ""

# Step 1: Install CDK dependencies
echo "📦 Installing CDK dependencies..."
cd cdk
npm install

# Step 2: Bootstrap CDK (if not already done)
echo "🔧 Bootstrapping CDK..."
npx cdk bootstrap aws://$AWS_ACCOUNT/$AWS_REGION || true

# Step 3: Deploy infrastructure
echo "🏗️  Deploying infrastructure..."
npx cdk deploy --require-approval never --outputs-file outputs.json

# Extract outputs
BACKEND_REPO=$(cat outputs.json | grep BackendRepoUri | cut -d'"' -f4)
FRONTEND_REPO=$(cat outputs.json | grep FrontendRepoUri | cut -d'"' -f4)
CLOUDFRONT_URL=$(cat outputs.json | grep CloudFrontURL | cut -d'"' -f4)

echo "✅ Infrastructure deployed!"
echo "Backend Repo: $BACKEND_REPO"
echo "Frontend Repo: $FRONTEND_REPO"
echo "CloudFront URL: $CLOUDFRONT_URL"

# Step 4: Build and push Docker images
echo "🐳 Building and pushing Docker images..."

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com

# Build and push backend
echo "Building backend..."
cd ../../backend
docker build -t watcher-backend .
docker tag watcher-backend:latest $BACKEND_REPO:latest
docker push $BACKEND_REPO:latest

# Build and push frontend
echo "Building frontend..."
cd ../frontend
docker build -t watcher-frontend --build-arg REACT_APP_API_URL=$CLOUDFRONT_URL .
docker tag watcher-frontend:latest $FRONTEND_REPO:latest
docker push $FRONTEND_REPO:latest

echo "✅ Docker images pushed!"

# Step 5: Update ECS services to pull new images
echo "🔄 Updating ECS services..."
aws ecs update-service --cluster WatcherStack-WatcherCluster* --service WatcherStack-BackendService* --force-new-deployment --region $AWS_REGION || true
aws ecs update-service --cluster WatcherStack-WatcherCluster* --service WatcherStack-FrontendService* --force-new-deployment --region $AWS_REGION || true
aws ecs update-service --cluster WatcherStack-WatcherCluster* --service WatcherStack-CeleryService* --force-new-deployment --region $AWS_REGION || true
aws ecs update-service --cluster WatcherStack-WatcherCluster* --service WatcherStack-BeatService* --force-new-deployment --region $AWS_REGION || true

echo "⏳ Waiting for services to stabilize (this may take 5-10 minutes)..."
sleep 60

# Step 6: Wait for services to be healthy
echo "⏳ Waiting for services to become healthy..."
echo "This may take 5-10 minutes..."
sleep 120

# Step 7: Run migrations via one-off task
echo "🗄️  Running database migrations..."
CLUSTER_NAME=$(aws ecs list-clusters --region $AWS_REGION | grep WatcherStack-WatcherCluster | cut -d'/' -f2 | tr -d '",')

# Get VPC and subnet info from the cluster
BACKEND_SERVICE=$(aws ecs list-services --cluster $CLUSTER_NAME --region $AWS_REGION | grep WatcherStack-BackendService | cut -d'/' -f3 | tr -d '",')
SERVICE_INFO=$(aws ecs describe-services --cluster $CLUSTER_NAME --services $BACKEND_SERVICE --region $AWS_REGION)
TASK_DEF=$(echo $SERVICE_INFO | grep -o '"taskDefinition": "[^"]*"' | head -1 | cut -d'"' -f4)
SUBNET=$(echo $SERVICE_INFO | grep -o '"subnets": \[[^]]*\]' | grep -o 'subnet-[a-z0-9]*' | head -1)
SG=$(echo $SERVICE_INFO | grep -o '"securityGroups": \[[^]]*\]' | grep -o 'sg-[a-z0-9]*' | head -1)

echo "Running migrations as one-off task..."
MIGRATE_TASK=$(aws ecs run-task \
    --cluster $CLUSTER_NAME \
    --task-definition $TASK_DEF \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNET],securityGroups=[$SG],assignPublicIp=DISABLED}" \
    --overrides '{"containerOverrides":[{"name":"backend","command":["python","manage.py","migrate"]}]}' \
    --region $AWS_REGION \
    --query 'tasks[0].taskArn' \
    --output text)

echo "Waiting for migration task to complete..."
aws ecs wait tasks-stopped --cluster $CLUSTER_NAME --tasks $MIGRATE_TASK --region $AWS_REGION

echo "📊 Populating public haunts..."
POPULATE_TASK=$(aws ecs run-task \
    --cluster $CLUSTER_NAME \
    --task-definition $TASK_DEF \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNET],securityGroups=[$SG],assignPublicIp=DISABLED}" \
    --overrides '{"containerOverrides":[{"name":"backend","command":["python","manage.py","populate_public_haunts"]}]}' \
    --region $AWS_REGION \
    --query 'tasks[0].taskArn' \
    --output text)

aws ecs wait tasks-stopped --cluster $CLUSTER_NAME --tasks $POPULATE_TASK --region $AWS_REGION

echo "👤 Creating demo user..."
DEMO_TASK=$(aws ecs run-task \
    --cluster $CLUSTER_NAME \
    --task-definition $TASK_DEF \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNET],securityGroups=[$SG],assignPublicIp=DISABLED}" \
    --overrides '{"containerOverrides":[{"name":"backend","command":["python","manage.py","populate_demo_data"]}]}' \
    --region $AWS_REGION \
    --query 'tasks[0].taskArn' \
    --output text)

aws ecs wait tasks-stopped --cluster $CLUSTER_NAME --tasks $DEMO_TASK --region $AWS_REGION

echo "✅ Database setup complete!"

echo ""
echo "🎉 Deployment Complete!"
echo ""
echo "📝 Access your application at:"
echo "   $CLOUDFRONT_URL"
echo ""
echo "🔑 Demo credentials:"
echo "   Email: demo@watcher.local"
echo "   Password: demo123"
echo ""
echo "⚠️  Note: It may take 5-10 minutes for all services to be fully operational."
echo "   Check ECS service status: aws ecs describe-services --cluster $CLUSTER_NAME --services WatcherStack-BackendService* --region $AWS_REGION"
