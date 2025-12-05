# Watcher AWS Deployment

Fast deployment to AWS ECS Fargate with CloudFront CDN.

## Quick Start

```bash
cd deployment
bash quick-deploy.sh
```

This will:
1. Deploy infrastructure (VPC, RDS, Redis, ECS, ALB, CloudFront)
2. Build and push Docker images to ECR
3. Deploy services to ECS Fargate
4. Run migrations and populate demo data
5. Provide CloudFront URL for access

## Prerequisites

- AWS CLI configured with credentials
- Docker installed and running
- Node.js 18+ installed
- ~20-30 minutes for full deployment

## What Gets Deployed

### Infrastructure
- **VPC**: 2 AZs with public/private subnets
- **RDS PostgreSQL**: t3.micro instance
- **ElastiCache Redis**: t3.micro instance
- **ECS Fargate**: 4 services (backend, frontend, celery, beat)
- **ALB**: Application Load Balancer
- **CloudFront**: CDN distribution

### Services
- **Backend**: Django API (1 task, 512 CPU, 1GB RAM)
- **Frontend**: React app (1 task, 256 CPU, 512MB RAM)
- **Celery Worker**: Background tasks (1 task, 512 CPU, 1GB RAM)
- **Celery Beat**: Task scheduler (1 task, 256 CPU, 512MB RAM)

## Estimated Costs

- RDS t3.micro: ~$15/month
- ElastiCache t3.micro: ~$12/month
- ECS Fargate: ~$30/month (4 tasks)
- ALB: ~$20/month
- CloudFront: ~$1/month (low traffic)
- NAT Gateway: ~$32/month
- **Total: ~$110/month**

## Manual Steps

If automatic migration/data population fails:

```bash
# Get cluster and task info
CLUSTER=$(aws ecs list-clusters | grep WatcherStack-WatcherCluster | cut -d'/' -f2 | tr -d '",')
TASK=$(aws ecs list-tasks --cluster $CLUSTER --service-name WatcherStack-BackendService | grep task | head -1 | cut -d'/' -f3 | tr -d '",')

# Run migrations
aws ecs execute-command \
  --cluster $CLUSTER \
  --task $TASK \
  --container backend \
  --command "python manage.py migrate" \
  --interactive

# Create superuser
aws ecs execute-command \
  --cluster $CLUSTER \
  --task $TASK \
  --container backend \
  --command "python manage.py createsuperuser" \
  --interactive

# Populate public haunts
aws ecs execute-command \
  --cluster $CLUSTER \
  --task $TASK \
  --container backend \
  --command "python manage.py populate_public_haunts" \
  --interactive

# Populate demo data
aws ecs execute-command \
  --cluster $CLUSTER \
  --task $TASK \
  --container backend \
  --command "python manage.py populate_demo_data" \
  --interactive
```

## Cleanup

To destroy all resources:

```bash
cd deployment/cdk
npx cdk destroy
```

## Troubleshooting

### Services not starting
Check ECS service events:
```bash
aws ecs describe-services --cluster WatcherStack-WatcherCluster* --services WatcherStack-BackendService*
```

### Database connection issues
Check security groups allow ECS -> RDS on port 5432

### CloudFront not working
Wait 10-15 minutes for distribution to fully deploy

### View logs
```bash
aws logs tail /aws/ecs/backend --follow
aws logs tail /aws/ecs/celery --follow
```

## Architecture

```
Internet
   ↓
CloudFront (CDN)
   ↓
Application Load Balancer
   ↓
ECS Fargate Services
   ├── Backend (Django)
   ├── Frontend (React)
   ├── Celery Worker
   └── Celery Beat
   ↓
RDS PostgreSQL + ElastiCache Redis
```

## Demo Credentials

- Email: `demo@watcher.local`
- Password: `demo123`

## Production Recommendations

For production use:
1. Use custom domain with Route53
2. Add SSL certificate to ALB
3. Enable RDS backups and Multi-AZ
4. Increase task counts for HA
5. Add CloudWatch alarms
6. Enable ECS Exec for debugging
7. Use Secrets Manager for sensitive data
8. Enable WAF on CloudFront
