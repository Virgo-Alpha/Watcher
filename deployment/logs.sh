#!/bin/bash
set -e

AWS_REGION=${AWS_REGION:-us-east-1}
SERVICE_TYPE=${1:-backend}
LINES=${2:-100}

echo "📋 Viewing logs for $SERVICE_TYPE"
echo ""

CLUSTER=$(aws ecs list-clusters --region $AWS_REGION --query 'clusterArns[?contains(@, `WatcherStack`)]' --output text | cut -d'/' -f2)

if [ -z "$CLUSTER" ]; then
    echo "❌ No cluster found"
    exit 1
fi

# Map service type to service name pattern
case $SERVICE_TYPE in
    backend)
        SERVICE_PATTERN="BackendService"
        ;;
    frontend)
        SERVICE_PATTERN="FrontendService"
        ;;
    celery)
        SERVICE_PATTERN="CeleryService"
        ;;
    beat)
        SERVICE_PATTERN="BeatService"
        ;;
    *)
        SERVICE_PATTERN="BackendService"
        ;;
esac

# Find the full service name
FULL_SERVICE=$(aws ecs list-services --cluster $CLUSTER --region $AWS_REGION --query 'serviceArns[]' --output text | grep -o "[^/]*$SERVICE_PATTERN[^/]*" | head -1)

if [ -z "$FULL_SERVICE" ]; then
    echo "❌ Service not found: $SERVICE_PATTERN"
    exit 1
fi

echo "Found service: $FULL_SERVICE"

# Get task ARN
TASK=$(aws ecs list-tasks --cluster $CLUSTER --service-name "$FULL_SERVICE" --region $AWS_REGION --query 'taskArns[0]' --output text)

if [ -z "$TASK" ] || [ "$TASK" = "None" ]; then
    echo "❌ No running tasks found for $FULL_SERVICE"
    echo "Service may still be starting up. Wait a moment and try again."
    exit 1
fi

TASK_ID=$(echo $TASK | cut -d'/' -f3)
echo "Found task: $TASK_ID"

# Get log group
LOG_GROUP="/ecs/WatcherStack"

# Get log stream
LOG_STREAM=$(aws logs describe-log-streams \
    --log-group-name $LOG_GROUP \
    --log-stream-name-prefix "$SERVICE_TYPE/$SERVICE_TYPE/$TASK_ID" \
    --region $AWS_REGION \
    --query 'logStreams[0].logStreamName' \
    --output text 2>/dev/null)

if [ -z "$LOG_STREAM" ] || [ "$LOG_STREAM" = "None" ]; then
    echo "⏳ Waiting for logs to appear..."
    sleep 5
    LOG_STREAM=$(aws logs describe-log-streams \
        --log-group-name $LOG_GROUP \
        --log-stream-name-prefix "$SERVICE_TYPE/$SERVICE_TYPE/$TASK_ID" \
        --region $AWS_REGION \
        --query 'logStreams[0].logStreamName' \
        --output text 2>/dev/null)
fi

if [ -z "$LOG_STREAM" ] || [ "$LOG_STREAM" = "None" ]; then
    echo "❌ No log stream found yet"
    echo "Task may still be starting. Available log streams:"
    aws logs describe-log-streams \
        --log-group-name $LOG_GROUP \
        --region $AWS_REGION \
        --query 'logStreams[*].logStreamName' \
        --output text | grep "$SERVICE_TYPE" | head -5
    exit 1
fi

echo "Streaming logs from: $LOG_STREAM"
echo ""

# Get recent logs
aws logs get-log-events \
    --log-group-name $LOG_GROUP \
    --log-stream-name "$LOG_STREAM" \
    --limit $LINES \
    --region $AWS_REGION \
    --query 'events[*].message' \
    --output text
