#!/bin/bash

SERVICE=${1:-backend}
AWS_REGION=${AWS_REGION:-us-east-1}

echo "📋 Viewing logs for: $SERVICE"
echo "Press Ctrl+C to exit"
echo ""

case $SERVICE in
    backend)
        aws logs tail /aws/ecs/backend --follow --region $AWS_REGION
        ;;
    frontend)
        aws logs tail /aws/ecs/frontend --follow --region $AWS_REGION
        ;;
    celery)
        aws logs tail /aws/ecs/celery --follow --region $AWS_REGION
        ;;
    beat)
        aws logs tail /aws/ecs/beat --follow --region $AWS_REGION
        ;;
    *)
        echo "Usage: bash logs.sh [backend|frontend|celery|beat]"
        echo "Default: backend"
        ;;
esac
