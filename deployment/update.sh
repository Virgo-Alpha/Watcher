#!/bin/bash
set -e

echo "🔄 Updating Watcher deployment"
echo "=============================="
echo ""

# Load environment
if [ -f ../.env ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
fi

export AWS_REGION=${AWS_REGION:-us-east-1}
export AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)

# Get outputs
if [ ! -f cdk/outputs.json ]; then
    echo "❌ outputs.json not found. Run ./deploy.sh first."
    exit 1
fi

BACKEND_REPO=$(cat cdk/outputs.json | grep -o '"BackendRepoUri": "[^"]*"' | cut -d'"' -f4)
FRONTEND_REPO=$(cat cdk/outputs.json | grep -o '"FrontendRepoUri": "[^"]*"' | cut -d'"' -f4)
ALB_DNS=$(cat cdk/outputs.json | grep -o '"LoadBalancerDNS": "[^"]*"' | cut -d'"' -f4)

echo "🐳 Building and pushing images..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com

cd ../backend
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

# Force new deployment
echo "🔄 Updating ECS services..."
CLUSTER=$(aws ecs list-clusters --region $AWS_REGION --query 'clusterArns[?contains(@, `WatcherStack`)]' --output text | cut -d'/' -f2)

# Get actual service names
BACKEND_SVC=$(aws ecs list-services --cluster $CLUSTER --region $AWS_REGION --query 'serviceArns[?contains(@, `BackendService`)]' --output text | cut -d'/' -f3)
FRONTEND_SVC=$(aws ecs list-services --cluster $CLUSTER --region $AWS_REGION --query 'serviceArns[?contains(@, `FrontendService`)]' --output text | cut -d'/' -f3)
CELERY_SVC=$(aws ecs list-services --cluster $CLUSTER --region $AWS_REGION --query 'serviceArns[?contains(@, `CeleryService`)]' --output text | cut -d'/' -f3)
BEAT_SVC=$(aws ecs list-services --cluster $CLUSTER --region $AWS_REGION --query 'serviceArns[?contains(@, `BeatService`)]' --output text | cut -d'/' -f3)

aws ecs update-service --cluster $CLUSTER --service $BACKEND_SVC --force-new-deployment --region $AWS_REGION --no-cli-pager >/dev/null &
aws ecs update-service --cluster $CLUSTER --service $FRONTEND_SVC --force-new-deployment --region $AWS_REGION --no-cli-pager >/dev/null &
aws ecs update-service --cluster $CLUSTER --service $CELERY_SVC --force-new-deployment --region $AWS_REGION --no-cli-pager >/dev/null &
aws ecs update-service --cluster $CLUSTER --service $BEAT_SVC --force-new-deployment --region $AWS_REGION --no-cli-pager >/dev/null &

wait

echo "⏳ Waiting for services to stabilize..."
aws ecs wait services-stable --cluster $CLUSTER --services $BACKEND_SVC --region $AWS_REGION
aws ecs wait services-stable --cluster $CLUSTER --services $FRONTEND_SVC --region $AWS_REGION

echo ""
echo "✅ Update complete!"
echo ""
