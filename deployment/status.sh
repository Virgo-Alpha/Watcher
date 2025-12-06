#!/bin/bash
set -e

AWS_REGION=${AWS_REGION:-us-east-1}

echo "📊 Watcher Deployment Status"
echo "============================"
echo ""

# Get cluster
CLUSTER=$(aws ecs list-clusters --region $AWS_REGION --query 'clusterArns[?contains(@, `WatcherStack`)]' --output text 2>/dev/null | cut -d'/' -f2)

if [ -z "$CLUSTER" ]; then
    echo "❌ No cluster found. Stack may not be deployed."
    exit 1
fi

echo "Cluster: $CLUSTER"
echo ""

# Get services
SERVICE_ARNS=$(aws ecs list-services --cluster $CLUSTER --region $AWS_REGION --query 'serviceArns[]' --output text)

for SERVICE_ARN in $SERVICE_ARNS; do
    # Extract service name from ARN
    SERVICE=$(echo "$SERVICE_ARN" | cut -d'/' -f3)
    
    echo "Service: $SERVICE"
    INFO=$(aws ecs describe-services --cluster $CLUSTER --services "$SERVICE" --region $AWS_REGION --query 'services[0]' --output json)
    
    STATUS=$(echo "$INFO" | jq -r '.status // "UNKNOWN"')
    DESIRED=$(echo "$INFO" | jq -r '.desiredCount // 0')
    RUNNING=$(echo "$INFO" | jq -r '.runningCount // 0')
    
    echo "  Status: $STATUS"
    echo "  Tasks: $RUNNING/$DESIRED"
    
    # Get latest event
    EVENT=$(echo "$INFO" | jq -r '.events[0].message // ""')
    if [ ! -z "$EVENT" ]; then
        echo "  Latest: $EVENT"
    fi
    echo ""
done

# Get URLs
if [ -f cdk/outputs.json ]; then
    CLOUDFRONT=$(jq -r '.WatcherStack.CloudFrontURL // ""' cdk/outputs.json)
    ALB=$(jq -r '.WatcherStack.LoadBalancerDNS // ""' cdk/outputs.json)
    
    echo "URLs:"
    if [ ! -z "$CLOUDFRONT" ]; then
        echo "  CloudFront: $CLOUDFRONT"
    fi
    if [ ! -z "$ALB" ]; then
        echo "  ALB: http://$ALB"
    fi
    echo ""
fi
