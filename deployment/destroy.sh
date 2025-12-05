#!/bin/bash
set -e

echo "🗑️  Destroying Watcher AWS infrastructure..."
echo "⚠️  This will delete all resources including databases!"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

cd cdk

# Empty ECR repositories first
echo "Emptying ECR repositories..."
AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)

aws ecr batch-delete-image \
    --repository-name watcher-backend \
    --image-ids "$(aws ecr list-images --repository-name watcher-backend --query 'imageIds[*]' --output json)" \
    --region $AWS_REGION || true

aws ecr batch-delete-image \
    --repository-name watcher-frontend \
    --image-ids "$(aws ecr list-images --repository-name watcher-frontend --query 'imageIds[*]' --output json)" \
    --region $AWS_REGION || true

# Destroy stack
echo "Destroying CDK stack..."
npx cdk destroy --force

echo "✅ Infrastructure destroyed!"
