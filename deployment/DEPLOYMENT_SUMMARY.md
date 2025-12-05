# Watcher AWS Deployment - Complete Summary

## 🎯 What Was Created

A complete AWS deployment infrastructure for Watcher using:
- **AWS CDK** (TypeScript) for infrastructure as code
- **ECS Fargate** for containerized services
- **CloudFront** for CDN and global distribution
- **RDS PostgreSQL** for database
- **ElastiCache Redis** for caching and task queue

## 📁 Deployment Structure

```
deployment/
├── START_HERE.md           # Quick start guide (read this first!)
├── QUICKSTART.md           # Detailed quick start
├── README.md               # Full documentation
├── fast-deploy.sh          # Main deployment script (USE THIS)
├── deploy.sh               # Alternative deployment script
├── status.sh               # Check deployment status
├── logs.sh                 # View service logs
├── build-and-push.sh       # Rebuild and redeploy images
├── run-migrations.sh       # Run migrations manually
├── destroy.sh              # Delete all resources
└── cdk/                    # AWS CDK infrastructure code
    ├── bin/app.ts          # CDK app entry point
    ├── lib/watcher-stack.ts # Main infrastructure stack
    ├── package.json        # CDK dependencies
    ├── tsconfig.json       # TypeScript config
    └── cdk.json            # CDK configuration
```

## 🚀 How to Deploy

### One Command:
```bash
cd deployment
bash fast-deploy.sh
```

### What It Does:
1. **Infrastructure** (10-15 min)
   - Creates VPC with public/private subnets across 2 AZs
   - Deploys RDS PostgreSQL (t3.micro)
   - Deploys ElastiCache Redis (t3.micro)
   - Creates ECS Cluster
   - Sets up Application Load Balancer
   - Creates CloudFront distribution
   - Creates ECR repositories

2. **Build & Push** (5-8 min)
   - Builds backend Docker image
   - Builds frontend Docker image
   - Pushes both to ECR

3. **Deploy Services** (3-5 min)
   - Backend API (Django)
   - Frontend (React)
   - Celery Worker (background tasks)
   - Celery Beat (scheduler)

4. **Initialize Data** (2-3 min)
   - Runs database migrations
   - Populates 6 public haunts
   - Creates demo user with sample data

**Total Time: 20-30 minutes**

## 🌐 Access Points

After deployment:
- **CloudFront URL**: `https://d1234567890.cloudfront.net` (takes 10-15 min to propagate)
- **ALB URL**: `http://watcher-alb-xxx.elb.amazonaws.com` (immediate access)

Use ALB URL for immediate testing, CloudFront for production.

## 🔑 Demo Credentials

- Email: `demo@watcher.local`
- Password: `demo123`

## 💰 Cost Breakdown

| Service | Type | Monthly Cost |
|---------|------|--------------|
| RDS PostgreSQL | t3.micro | ~$15 |
| ElastiCache Redis | t3.micro | ~$12 |
| ECS Fargate | 4 tasks | ~$30 |
| Application Load Balancer | - | ~$20 |
| NAT Gateway | 1 gateway | ~$32 |
| CloudFront | Low traffic | ~$1 |
| **Total** | | **~$110/month** |

## 📊 Infrastructure Details

### VPC Configuration
- **CIDR**: Auto-assigned
- **Availability Zones**: 2
- **Public Subnets**: 2 (for ALB)
- **Private Subnets**: 2 (for ECS, RDS, Redis)
- **NAT Gateways**: 1

### ECS Services

| Service | CPU | Memory | Count | Purpose |
|---------|-----|--------|-------|---------|
| Backend | 512 | 1024 MB | 1 | Django REST API |
| Frontend | 256 | 512 MB | 1 | React app |
| Celery | 512 | 1024 MB | 1 | Background worker |
| Beat | 256 | 512 MB | 1 | Task scheduler |

### Database
- **Engine**: PostgreSQL 15
- **Instance**: db.t3.micro
- **Storage**: 20 GB (auto-scaling to 100 GB)
- **Backups**: Disabled (enable for production)
- **Multi-AZ**: Disabled (enable for production)

### Redis
- **Engine**: Redis
- **Node Type**: cache.t3.micro
- **Nodes**: 1

### Load Balancer
- **Type**: Application Load Balancer
- **Scheme**: Internet-facing
- **Listeners**: HTTP (80)
- **Target Groups**: 2 (backend, frontend)
- **Health Checks**: Enabled

### CloudFront
- **Origin**: ALB
- **Protocol**: HTTPS redirect
- **Caching**: Disabled (for API compatibility)
- **Behaviors**: 
  - Default → Frontend
  - `/api/*` → Backend

## 🛠️ Useful Commands

### Check Status
```bash
cd deployment
bash status.sh
```

### View Logs
```bash
bash logs.sh backend    # Backend logs
bash logs.sh frontend   # Frontend logs
bash logs.sh celery     # Celery worker logs
bash logs.sh beat       # Celery beat logs
```

### Rebuild and Redeploy
```bash
bash build-and-push.sh
```

### Run Migrations
```bash
bash run-migrations.sh
```

### Destroy Everything
```bash
bash destroy.sh
```

## 🔧 Manual Operations

### Access ECS Task
```bash
# Get cluster name
CLUSTER=$(aws ecs list-clusters | grep WatcherStack-WatcherCluster | cut -d'/' -f2 | tr -d '",')

# Get task ARN
TASK=$(aws ecs list-tasks --cluster $CLUSTER --service-name WatcherStack-BackendService | grep task | head -1 | cut -d'/' -f3 | tr -d '",')

# Execute command
aws ecs execute-command \
  --cluster $CLUSTER \
  --task $TASK \
  --container backend \
  --command "python manage.py shell" \
  --interactive
```

### View CloudWatch Logs
```bash
aws logs tail /aws/ecs/backend --follow
aws logs tail /aws/ecs/celery --follow
```

### Update Service
```bash
aws ecs update-service \
  --cluster WatcherStack-WatcherCluster* \
  --service WatcherStack-BackendService \
  --force-new-deployment
```

## 🔒 Security Considerations

### Current Setup (Development)
- ✅ VPC with public/private subnets
- ✅ Security groups restricting access
- ✅ Database in private subnet
- ✅ Redis in private subnet
- ✅ Secrets in environment variables
- ⚠️ HTTP only (no SSL)
- ⚠️ Secrets in task definitions
- ⚠️ No WAF
- ⚠️ No database backups

### Production Recommendations
1. **SSL/TLS**: Add ACM certificate to ALB
2. **Secrets**: Use AWS Secrets Manager
3. **WAF**: Add AWS WAF to CloudFront
4. **Backups**: Enable RDS automated backups
5. **Multi-AZ**: Enable RDS Multi-AZ
6. **Monitoring**: Add CloudWatch alarms
7. **Logging**: Enable VPC Flow Logs
8. **IAM**: Use least-privilege IAM roles
9. **Domain**: Use Route53 with custom domain
10. **Scaling**: Add auto-scaling policies

## 🐛 Troubleshooting

### Services Not Starting
```bash
# Check service status
bash status.sh

# View logs
bash logs.sh backend

# Describe service
aws ecs describe-services \
  --cluster WatcherStack-WatcherCluster* \
  --services WatcherStack-BackendService
```

### Database Connection Issues
- Check security groups allow ECS → RDS on port 5432
- Verify DATABASE_URL in task definition
- Check RDS instance status

### Redis Connection Issues
- Check security groups allow ECS → Redis on port 6379
- Verify REDIS_URL in task definition
- Check ElastiCache cluster status

### CloudFront Not Working
- Wait 10-15 minutes for distribution to deploy
- Use ALB URL for immediate access
- Check CloudFront distribution status

### Migrations Failed
```bash
bash run-migrations.sh
```

## 📈 Scaling for Production

### Increase Task Counts
Edit `deployment/cdk/lib/watcher-stack.ts`:
```typescript
desiredCount: 2,  // Change from 1 to 2 or more
```

### Enable Auto-Scaling
Add to ECS service:
```typescript
const scaling = service.autoScaleTaskCount({
  minCapacity: 1,
  maxCapacity: 10,
});

scaling.scaleOnCpuUtilization('CpuScaling', {
  targetUtilizationPercent: 70,
});
```

### Upgrade Instance Types
```typescript
// RDS
instanceType: ec2.InstanceType.of(
  ec2.InstanceClass.T3,
  ec2.InstanceSize.SMALL  // or MEDIUM
),

// Redis
cacheNodeType: 'cache.t3.small',  // or medium
```

## 🔄 CI/CD Integration

### GitHub Actions Example
```yaml
name: Deploy to AWS
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - run: cd deployment && bash build-and-push.sh
```

## 📚 Additional Resources

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [ECS Fargate Documentation](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html)
- [CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [RDS Documentation](https://docs.aws.amazon.com/rds/)

## ✅ Deployment Checklist

- [ ] AWS CLI configured
- [ ] Docker installed and running
- [ ] Node.js 18+ installed
- [ ] LLM_API_KEY in .env file
- [ ] Run `bash fast-deploy.sh`
- [ ] Wait 20-30 minutes
- [ ] Access ALB URL
- [ ] Login with demo credentials
- [ ] Test creating a haunt
- [ ] Wait for CloudFront (optional)
- [ ] Access CloudFront URL

## 🎉 Success Criteria

Your deployment is successful when:
1. ✅ All 4 ECS services show 1/1 running
2. ✅ ALB health checks pass
3. ✅ You can access the app via ALB URL
4. ✅ You can login with demo credentials
5. ✅ You see 6 public haunts
6. ✅ You can create a new haunt
7. ✅ CloudFront URL works (after 10-15 min)

---

**Questions or issues?** Check the logs with `bash logs.sh backend` or open an issue on GitHub.
