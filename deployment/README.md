# Watcher AWS Deployment

Deploy Watcher to AWS ECS Fargate with CloudFront CDN.

## Prerequisites

- AWS CLI configured with credentials
- Docker installed and running
- Node.js 18+ installed
- LLM_API_KEY in `../.env` file

## Local vs Production Configurations

Watcher has **two separate Docker configurations**:

### Local Development (`../docker-compose.yml`)
- **Frontend**: Uses `Dockerfile.dev` with React dev server
- **Hot reload**: Code changes reflect immediately
- **Debug mode**: Enabled for easier development
- **Ports**: Frontend 3000, Backend 8000, DB 5432, Redis 6379
- **API URL**: Uses absolute URL `http://localhost:8000/api/v1` (set via `REACT_APP_API_URL`)
- **Use for**: Day-to-day development work

### Production (`../docker-compose.prod.yml` and AWS)
- **Frontend**: Uses production `Dockerfile` with nginx serving static build
- **Optimized**: Minified assets, production settings
- **Debug mode**: Disabled
- **Ports (local)**: Frontend 80, Backend 8000, DB 5433, Redis 6380
- **API URL**: Uses relative URL `/api/v1` (automatic when `REACT_APP_API_URL` is undefined or empty)
- **Use for**: Testing production build locally before AWS deployment

**Note**: The frontend automatically detects whether to use absolute or relative API URLs based on the `REACT_APP_API_URL` environment variable. In production, leaving this undefined or empty enables relative URLs, which work seamlessly with CloudFront and ALB routing.

## Quick Start

```bash
# First-time deployment (20-30 min)
./deploy.sh

# Update code after changes (5-10 min)
./update.sh

# Check deployment status
./status.sh

# View logs
./logs.sh BackendService   # or FrontendService, CeleryService, BeatService

# Destroy everything
./destroy.sh
```

## Testing Production Build Locally

Before deploying to AWS, test the production build on your machine:

```bash
# From project root
docker-compose -f docker-compose.prod.yml up -d

# Run migrations and setup demo data
docker-compose -f docker-compose.prod.yml exec web python manage.py populate_demo_data

# Access at http://localhost (port 80)
# Backend API: http://localhost:8000/api/v1

# Test login
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@watcher.local","password":"demo123"}'

# Stop when done
docker-compose -f docker-compose.prod.yml down
```

## Verifying AWS Deployment

After deployment completes, verify everything is working:

```bash
# Get CloudFront URL from outputs
CLOUDFRONT_URL=$(cat cdk-outputs.json | grep -o '"CloudFrontURL": "[^"]*"' | cut -d'"' -f4)

# Test frontend
curl -s $CLOUDFRONT_URL/ | head -20

# Test backend API
curl -X POST $CLOUDFRONT_URL/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@watcher.local","password":"demo123"}'

# Check ECS services
CLUSTER=$(aws ecs list-clusters --query 'clusterArns[?contains(@, `WatcherStack`)]' --output text | cut -d'/' -f2)
aws ecs describe-services --cluster $CLUSTER \
  --services $(aws ecs list-services --cluster $CLUSTER --query 'serviceArns' --output text | tr '\t' ' ') \
  --query 'services[*].[serviceName,desiredCount,runningCount,status]' \
  --output table
```

## How It Works

### First Deployment (`deploy.sh`)

1. **Deploy infrastructure** - Creates VPC, RDS, Redis, ECS cluster, ECR repos, ALB, CloudFront
   - All ECS services start with `desiredCount: 0` (no tasks running)
   - This prevents "image not found" errors during initial deployment

2. **Build and push images** - Builds Docker images and pushes to ECR
   - Backend image with Django app
   - Frontend image with React app

3. **Scale up services** - Updates ECS services to `desiredCount: 1`
   - Now images exist in ECR, so tasks can start successfully
   - Waits for services to stabilize

4. **Run migrations** - Executes one-off tasks for database setup
   - Runs Django migrations
   - Populates public haunts
   - Creates demo user

### Updates (`update.sh`)

For code changes after initial deployment:

1. Builds new Docker images
2. Pushes to ECR
3. Forces ECS service redeployment
4. Waits for services to stabilize

No infrastructure changes, much faster than full deployment.

## Architecture

```
CloudFront (CDN)
    ↓
Application Load Balancer
    ↓
┌─────────────┬──────────────┬──────────────┬──────────────┐
│   Backend   │   Frontend   │    Celery    │     Beat     │
│  (Django)   │   (React)    │   (Worker)   │ (Scheduler)  │
└─────────────┴──────────────┴──────────────┴──────────────┘
         ↓                                    ↓
    ┌────────┐                          ┌─────────┐
    │  RDS   │                          │  Redis  │
    │ (PG)   │                          │ (Cache) │
    └────────┘                          └─────────┘
```

## Cost Estimate

- **ECS Fargate**: ~$30-50/month (4 services)
- **RDS t3.micro**: ~$15/month
- **ElastiCache t3.micro**: ~$12/month
- **ALB**: ~$20/month
- **CloudFront**: ~$1-5/month (low traffic)
- **NAT Gateway**: ~$32/month
- **Total**: ~$110-135/month

## Troubleshooting

### Services not starting

```bash
./status.sh  # Check service status
./logs.sh BackendService  # View logs
```

Common issues:
- Image not found: Run `./update.sh` to rebuild and push images
- Health check failing: Check `/api/v1/health/` endpoint
- Database connection: Verify RDS security group allows ECS access

### Stack stuck in ROLLBACK

This happens when services can't stabilize during initial deployment. The fix:

1. Services now start with `desiredCount: 0`
2. Images are pushed to ECR
3. Services are scaled up after images exist

If you still hit this:

```bash
./destroy.sh  # Clean up
./deploy.sh   # Try again
```

### CloudFront not working

CloudFront takes 10-15 minutes to propagate. Use ALB URL for immediate access:

```bash
# Get ALB URL
cat cdk/outputs.json | grep LoadBalancerDNS
```

## Manual Operations

### Run Django management commands

```bash
CLUSTER=$(aws ecs list-clusters --query 'clusterArns[?contains(@, `WatcherStack`)]' --output text | cut -d'/' -f2)
TASK_DEF=$(aws ecs describe-services --cluster $CLUSTER --services WatcherStack-BackendService --query 'services[0].taskDefinition' --output text)
SUBNET=$(aws ecs describe-services --cluster $CLUSTER --services WatcherStack-BackendService --query 'services[0].networkConfiguration.awsvpcConfiguration.subnets[0]' --output text)
SG=$(aws ecs describe-services --cluster $CLUSTER --services WatcherStack-BackendService --query 'services[0].networkConfiguration.awsvpcConfiguration.securityGroups[0]' --output text)

aws ecs run-task \
    --cluster $CLUSTER \
    --task-definition $TASK_DEF \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNET],securityGroups=[$SG],assignPublicIp=DISABLED}" \
    --overrides '{"containerOverrides":[{"name":"backend","command":["python","manage.py","YOUR_COMMAND"]}]}'
```

### Scale services

```bash
CLUSTER=$(aws ecs list-clusters --query 'clusterArns[?contains(@, `WatcherStack`)]' --output text | cut -d'/' -f2)

# Scale up
aws ecs update-service --cluster $CLUSTER --service WatcherStack-BackendService --desired-count 2

# Scale down
aws ecs update-service --cluster $CLUSTER --service WatcherStack-BackendService --desired-count 0
```

## Files

- `deploy.sh` - Full deployment (first time)
- `update.sh` - Update code only (after changes)
- `status.sh` - Check deployment status
- `logs.sh` - View service logs
- `destroy.sh` - Delete everything
- `cdk/` - Infrastructure as code (CDK)
