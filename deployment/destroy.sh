#!/bin/bash
set -e

echo "🗑️  Destroying Watcher deployment"
echo "================================="
echo ""
echo "⚠️  This will delete all resources including:"
echo "   - ECS services and tasks"
echo "   - RDS database (all data will be lost)"
echo "   - Redis cache"
echo "   - Load balancer"
echo "   - CloudFront distribution"
echo "   - ECR repositories and images"
echo ""
read -p "Are you sure? Type 'yes' to confirm: " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Cancelled"
    exit 0
fi

export AWS_REGION=${AWS_REGION:-us-east-1}

echo ""
echo "🔄 Scaling down services to 0..."
CLUSTER=$(aws ecs list-clusters --region $AWS_REGION --query 'clusterArns[?contains(@, `WatcherStack`)]' --output text 2>/dev/null | cut -d'/' -f2)

if [ ! -z "$CLUSTER" ]; then
    aws ecs update-service --cluster $CLUSTER --service WatcherStack-BackendService --desired-count 0 --region $AWS_REGION --no-cli-pager 2>/dev/null || true
    aws ecs update-service --cluster $CLUSTER --service WatcherStack-FrontendService --desired-count 0 --region $AWS_REGION --no-cli-pager 2>/dev/null || true
    aws ecs update-service --cluster $CLUSTER --service WatcherStack-CeleryService --desired-count 0 --region $AWS_REGION --no-cli-pager 2>/dev/null || true
    aws ecs update-service --cluster $CLUSTER --service WatcherStack-BeatService --desired-count 0 --region $AWS_REGION --no-cli-pager 2>/dev/null || true
    
    echo "⏳ Waiting for tasks to stop..."
    sleep 30
fi

echo ""
echo "🗑️  Destroying CDK stack..."
cd cdk
npx cdk destroy --force

echo ""
echo "✅ Destruction complete!"
echo ""
