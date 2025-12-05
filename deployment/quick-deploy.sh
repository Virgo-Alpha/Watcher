#!/bin/bash
set -e

echo "⚡ Quick AWS Deployment Script"
echo "This will deploy Watcher to AWS ECS Fargate with CloudFront"
echo ""

# Check prerequisites
command -v aws >/dev/null 2>&1 || { echo "❌ AWS CLI not found. Install it first."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found. Install it first."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js not found. Install it first."; exit 1; }

# Check AWS credentials
aws sts get-caller-identity >/dev/null 2>&1 || { echo "❌ AWS credentials not configured. Run 'aws configure' first."; exit 1; }

echo "✅ Prerequisites check passed"
echo ""

# Run deployment
bash deploy.sh
