#!/bin/bash

echo "🔍 Checking Prerequisites for AWS Deployment"
echo "=============================================="
echo ""

ERRORS=0

# Check AWS CLI
if command -v aws >/dev/null 2>&1; then
    AWS_VERSION=$(aws --version 2>&1 | cut -d' ' -f1)
    echo "✅ AWS CLI: $AWS_VERSION"
else
    echo "❌ AWS CLI not found"
    echo "   Install: https://aws.amazon.com/cli/"
    ERRORS=$((ERRORS+1))
fi

# Check AWS credentials
if aws sts get-caller-identity >/dev/null 2>&1; then
    AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    AWS_USER=$(aws sts get-caller-identity --query Arn --output text | cut -d'/' -f2)
    echo "✅ AWS Credentials: $AWS_USER (Account: $AWS_ACCOUNT)"
else
    echo "❌ AWS credentials not configured"
    echo "   Run: aws configure"
    ERRORS=$((ERRORS+1))
fi

# Check Docker
if command -v docker >/dev/null 2>&1; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
    echo "✅ Docker: $DOCKER_VERSION"
    
    # Check if Docker is running
    if docker ps >/dev/null 2>&1; then
        echo "✅ Docker daemon: Running"
    else
        echo "❌ Docker daemon not running"
        echo "   Start Docker Desktop or run: sudo systemctl start docker"
        ERRORS=$((ERRORS+1))
    fi
else
    echo "❌ Docker not found"
    echo "   Install: https://docs.docker.com/get-docker/"
    ERRORS=$((ERRORS+1))
fi

# Check Node.js
if command -v node >/dev/null 2>&1; then
    NODE_VERSION=$(node --version)
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1 | tr -d 'v')
    if [ "$NODE_MAJOR" -ge 18 ]; then
        echo "✅ Node.js: $NODE_VERSION"
    else
        echo "⚠️  Node.js: $NODE_VERSION (18+ recommended)"
    fi
else
    echo "❌ Node.js not found"
    echo "   Install: https://nodejs.org/"
    ERRORS=$((ERRORS+1))
fi

# Check npm
if command -v npm >/dev/null 2>&1; then
    NPM_VERSION=$(npm --version)
    echo "✅ npm: $NPM_VERSION"
else
    echo "❌ npm not found (comes with Node.js)"
    ERRORS=$((ERRORS+1))
fi

# Check .env file
if [ -f ../.env ]; then
    echo "✅ .env file: Found"
    
    # Check for LLM_API_KEY
    if grep -q "^LLM_API_KEY=" ../.env; then
        API_KEY=$(grep "^LLM_API_KEY=" ../.env | cut -d'=' -f2)
        if [ ! -z "$API_KEY" ] && [ "$API_KEY" != "your-api-key-here" ]; then
            echo "✅ LLM_API_KEY: Configured (${API_KEY:0:10}...)"
        else
            echo "❌ LLM_API_KEY: Not configured in .env"
            echo "   Get key from: https://aistudio.google.com/app/apikey"
            ERRORS=$((ERRORS+1))
        fi
    else
        echo "❌ LLM_API_KEY: Missing from .env"
        ERRORS=$((ERRORS+1))
    fi
else
    echo "❌ .env file not found"
    echo "   Copy from: cp .env.example .env"
    ERRORS=$((ERRORS+1))
fi

echo ""
echo "=============================================="

if [ $ERRORS -eq 0 ]; then
    echo "✅ All prerequisites met!"
    echo ""
    echo "Ready to deploy:"
    echo "  cd deployment"
    echo "  bash fast-deploy.sh"
    exit 0
else
    echo "❌ $ERRORS error(s) found"
    echo ""
    echo "Fix the errors above and try again."
    exit 1
fi
