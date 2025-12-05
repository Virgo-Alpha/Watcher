# Quick Command Reference

## Deployment

```bash
# Check prerequisites
bash check-prerequisites.sh

# Deploy everything
bash fast-deploy.sh

# Alternative deployment
bash deploy.sh
```

## Monitoring

```bash
# Check deployment status
bash status.sh

# View backend logs
bash logs.sh backend

# View frontend logs
bash logs.sh frontend

# View celery logs
bash logs.sh celery

# View beat logs
bash logs.sh beat
```

## Maintenance

```bash
# Rebuild and redeploy images
bash build-and-push.sh

# Run migrations manually
bash run-migrations.sh

# Destroy all resources
bash destroy.sh
```

## AWS CLI Commands

```bash
# List ECS services
aws ecs list-services --cluster WatcherStack-WatcherCluster*

# Describe service
aws ecs describe-services \
  --cluster WatcherStack-WatcherCluster* \
  --services WatcherStack-BackendService

# View CloudWatch logs
aws logs tail /aws/ecs/backend --follow

# Update service (force redeploy)
aws ecs update-service \
  --cluster WatcherStack-WatcherCluster* \
  --service WatcherStack-BackendService \
  --force-new-deployment

# Get CloudFront distribution
aws cloudfront list-distributions \
  --query 'DistributionList.Items[?contains(Comment, `Watcher`)].DomainName'

# Check RDS status
aws rds describe-db-instances \
  --query 'DBInstances[?contains(DBInstanceIdentifier, `watcher`)].DBInstanceStatus'

# Check Redis status
aws elasticache describe-cache-clusters \
  --query 'CacheClusters[?contains(CacheClusterId, `watcher`)].CacheClusterStatus'
```

## Docker Commands

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  021891601803.dkr.ecr.us-east-1.amazonaws.com

# Build backend
docker build -t watcher-backend ../backend

# Build frontend
docker build -t watcher-frontend ../frontend

# Tag and push
docker tag watcher-backend:latest <ECR_REPO>:latest
docker push <ECR_REPO>:latest
```

## CDK Commands

```bash
cd cdk

# Install dependencies
npm install

# Synthesize CloudFormation
npx cdk synth

# Deploy
npx cdk deploy

# Destroy
npx cdk destroy

# Diff changes
npx cdk diff

# List stacks
npx cdk list
```

## Troubleshooting

```bash
# Check if stack exists
aws cloudformation describe-stacks --stack-name WatcherStack

# Get stack outputs
aws cloudformation describe-stacks \
  --stack-name WatcherStack \
  --query 'Stacks[0].Outputs'

# Get ECS task details
CLUSTER=$(aws ecs list-clusters | grep WatcherStack | cut -d'/' -f2 | tr -d '",')
TASK=$(aws ecs list-tasks --cluster $CLUSTER --service-name WatcherStack-BackendService | grep task | head -1 | cut -d'/' -f3 | tr -d '",')

# Execute command in task
aws ecs execute-command \
  --cluster $CLUSTER \
  --task $TASK \
  --container backend \
  --command "python manage.py shell" \
  --interactive

# View task logs
aws logs tail /aws/ecs/backend --follow --since 10m

# Check service events
aws ecs describe-services \
  --cluster $CLUSTER \
  --services WatcherStack-BackendService \
  --query 'services[0].events[0:5]'
```

## Environment Variables

```bash
# Set AWS region
export AWS_REGION=us-east-1

# Set AWS profile
export AWS_PROFILE=default

# Load .env file
export $(cat ../.env | grep -v '^#' | xargs)
```

## Useful Queries

```bash
# Get all running tasks
aws ecs list-tasks --cluster $CLUSTER --desired-status RUNNING

# Get task IPs
aws ecs describe-tasks \
  --cluster $CLUSTER \
  --tasks $(aws ecs list-tasks --cluster $CLUSTER --query 'taskArns[0]' --output text) \
  --query 'tasks[0].attachments[0].details[?name==`privateIPv4Address`].value' \
  --output text

# Get ALB DNS
aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[?contains(LoadBalancerName, `Watcher`)].DNSName' \
  --output text

# Get CloudFront URL
aws cloudfront list-distributions \
  --query 'DistributionList.Items[?contains(Comment, `Watcher`)].DomainName' \
  --output text
```
