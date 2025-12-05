#!/bin/bash

echo "📊 Watcher Deployment Status"
echo "=============================="
echo ""

AWS_REGION=${AWS_REGION:-us-east-1}

# Check if stack exists
STACK_STATUS=$(aws cloudformation describe-stacks --stack-name WatcherStack --region $AWS_REGION --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$STACK_STATUS" = "NOT_FOUND" ]; then
    echo "❌ Stack not deployed yet"
    echo ""
    echo "Run: cd deployment && bash fast-deploy.sh"
    exit 0
fi

echo "Stack Status: $STACK_STATUS"
echo ""

# Get outputs
if [ -f cdk/outputs.json ]; then
    CLOUDFRONT_URL=$(cat cdk/outputs.json | grep -o '"WatcherStack.CloudFrontURL": "[^"]*"' | cut -d'"' -f4)
    ALB_DNS=$(cat cdk/outputs.json | grep -o '"WatcherStack.LoadBalancerDNS": "[^"]*"' | cut -d'"' -f4)
    
    echo "🌐 URLs:"
    echo "   CloudFront: $CLOUDFRONT_URL"
    echo "   ALB: http://$ALB_DNS"
    echo ""
fi

# Get cluster
CLUSTER=$(aws ecs list-clusters --region $AWS_REGION --query 'clusterArns[?contains(@, `WatcherStack`)]' --output text | cut -d'/' -f2)

if [ ! -z "$CLUSTER" ]; then
    echo "🐳 ECS Services:"
    
    # Backend
    BACKEND=$(aws ecs describe-services --cluster $CLUSTER --services WatcherStack-BackendService --region $AWS_REGION --query 'services[0].[runningCount,desiredCount]' --output text 2>/dev/null)
    echo "   Backend: $BACKEND (running/desired)"
    
    # Frontend
    FRONTEND=$(aws ecs describe-services --cluster $CLUSTER --services WatcherStack-FrontendService --region $AWS_REGION --query 'services[0].[runningCount,desiredCount]' --output text 2>/dev/null)
    echo "   Frontend: $FRONTEND (running/desired)"
    
    # Celery
    CELERY=$(aws ecs describe-services --cluster $CLUSTER --services WatcherStack-CeleryService --region $AWS_REGION --query 'services[0].[runningCount,desiredCount]' --output text 2>/dev/null)
    echo "   Celery: $CELERY (running/desired)"
    
    # Beat
    BEAT=$(aws ecs describe-services --cluster $CLUSTER --services WatcherStack-BeatService --region $AWS_REGION --query 'services[0].[runningCount,desiredCount]' --output text 2>/dev/null)
    echo "   Beat: $BEAT (running/desired)"
    echo ""
fi

# Database
DB_STATUS=$(aws rds describe-db-instances --region $AWS_REGION --query 'DBInstances[?contains(DBInstanceIdentifier, `watcherstack`)].DBInstanceStatus' --output text 2>/dev/null)
if [ ! -z "$DB_STATUS" ]; then
    echo "🗄️  Database: $DB_STATUS"
fi

# Redis
REDIS_STATUS=$(aws elasticache describe-cache-clusters --region $AWS_REGION --query 'CacheClusters[?contains(CacheClusterId, `watcherstack`)].CacheClusterStatus' --output text 2>/dev/null)
if [ ! -z "$REDIS_STATUS" ]; then
    echo "📦 Redis: $REDIS_STATUS"
fi

echo ""
echo "🔑 Demo Credentials:"
echo "   Email: demo@watcher.local"
echo "   Password: demo123"
echo ""
