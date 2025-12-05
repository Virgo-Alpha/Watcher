#!/bin/bash
set -e

echo "🐳 Building and pushing Docker images to ECR..."

# Load environment
if [ -f ../.env ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
fi

AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)

# Get ECR repositories from CDK outputs
if [ ! -f cdk/outputs.json ]; then
    echo "❌ outputs.json not found. Run deployment first."
    exit 1
fi

BACKEND_REPO=$(cat cdk/outputs.json | grep BackendRepoUri | cut -d'"' -f4)
FRONTEND_REPO=$(cat cdk/outputs.json | grep FrontendRepoUri | cut -d'"' -f4)
CLOUDFRONT_URL=$(cat cdk/outputs.json | grep CloudFrontURL | cut -d'"' -f4)

echo "Backend Repo: $BACKEND_REPO"
echo "Frontend Repo: $FRONTEND_REPO"

# Login to ECR
echo "Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com

# Build and push backend
echo "Building backend..."
cd ../backend
docker build -t watcher-backend .
docker tag watcher-backend:latest $BACKEND_REPO:latest
echo "Pushing backend..."
docker push $BACKEND_REPO:latest

# Build and push frontend
echo "Building frontend..."
cd ../frontend
docker build -t watcher-frontend --build-arg REACT_APP_API_URL=$CLOUDFRONT_URL .
docker tag watcher-frontend:latest $FRONTEND_REPO:latest
echo "Pushing frontend..."
docker push $FRONTEND_REPO:latest

echo "✅ Images pushed successfully!"

# Update ECS services
echo "🔄 Updating ECS services..."
CLUSTER=$(aws ecs list-clusters --region $AWS_REGION | grep WatcherStack-WatcherCluster | cut -d'/' -f2 | tr -d '",')

aws ecs update-service --cluster $CLUSTER --service WatcherStack-BackendService --force-new-deployment --region $AWS_REGION || true
aws ecs update-service --cluster $CLUSTER --service WatcherStack-FrontendService --force-new-deployment --region $AWS_REGION || true
aws ecs update-service --cluster $CLUSTER --service WatcherStack-CeleryService --force-new-deployment --region $AWS_REGION || true
aws ecs update-service --cluster $CLUSTER --service WatcherStack-BeatService --force-new-deployment --region $AWS_REGION || true

echo "✅ Services updated!"
