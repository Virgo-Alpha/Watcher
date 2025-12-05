#!/bin/bash
set -e

echo "🗄️  Running database migrations on ECS..."

AWS_REGION=${AWS_REGION:-us-east-1}

# Get cluster and task
CLUSTER=$(aws ecs list-clusters --region $AWS_REGION | grep WatcherStack-WatcherCluster | cut -d'/' -f2 | tr -d '",')
TASK=$(aws ecs list-tasks --cluster $CLUSTER --service-name WatcherStack-BackendService --region $AWS_REGION | grep task | head -1 | cut -d'/' -f3 | tr -d '",')

if [ -z "$TASK" ]; then
    echo "❌ No backend task found. Make sure services are running."
    exit 1
fi

echo "Running on cluster: $CLUSTER"
echo "Task: $TASK"

# Run migrations
echo "Running migrate..."
aws ecs execute-command \
    --cluster $CLUSTER \
    --task $TASK \
    --container backend \
    --command "python manage.py migrate" \
    --interactive \
    --region $AWS_REGION

# Populate public haunts
echo "Populating public haunts..."
aws ecs execute-command \
    --cluster $CLUSTER \
    --task $TASK \
    --container backend \
    --command "python manage.py populate_public_haunts" \
    --interactive \
    --region $AWS_REGION

# Populate demo data
echo "Populating demo data..."
aws ecs execute-command \
    --cluster $CLUSTER \
    --task $TASK \
    --container backend \
    --command "python manage.py populate_demo_data" \
    --interactive \
    --region $AWS_REGION

echo "✅ Done!"
