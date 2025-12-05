# Quick Deployment Guide

Deploy Watcher to AWS in under 30 minutes.

## Prerequisites

```bash
# Check you have everything
aws --version          # AWS CLI
docker --version       # Docker
node --version         # Node.js 18+
aws sts get-caller-identity  # AWS credentials configured
```

## Deploy

```bash
cd deployment
bash fast-deploy.sh
```

That's it! The script will:
1. Deploy infrastructure (VPC, RDS, Redis, ECS, ALB, CloudFront)
2. Build and push Docker images
3. Deploy services
4. Run migrations
5. Populate demo data

## Access

After deployment completes, you'll see:

```
🌐 CloudFront URL: https://d1234567890.cloudfront.net
🔗 ALB URL: http://watcher-alb-123456789.us-east-1.elb.amazonaws.com

🔑 Demo Login:
   Email: demo@watcher.local
   Password: demo123
```

Use the **ALB URL** for immediate access (CloudFront takes 10-15 min to propagate).

## What You Get

- **Backend API**: Django REST Framework on ECS Fargate
- **Frontend**: React app on ECS Fargate
- **Workers**: Celery + Beat for background scraping
- **Database**: RDS PostgreSQL (t3.micro)
- **Cache**: ElastiCache Redis (t3.micro)
- **CDN**: CloudFront distribution
- **Demo Data**: 6 public haunts + demo user with sample data

## Cost

Approximately **$110/month** for all resources:
- RDS: ~$15/mo
- Redis: ~$12/mo
- ECS Fargate: ~$30/mo
- ALB: ~$20/mo
- NAT Gateway: ~$32/mo
- CloudFront: ~$1/mo

## Cleanup

```bash
cd deployment
bash destroy.sh
```

## Troubleshooting

### Services not starting
```bash
# Check service status
aws ecs describe-services --cluster WatcherStack-WatcherCluster* --services WatcherStack-BackendService*

# View logs
aws logs tail /aws/ecs/backend --follow
```

### Need to re-run migrations
```bash
cd deployment
bash run-migrations.sh
```

### Rebuild and redeploy
```bash
cd deployment
bash build-and-push.sh
```

## Next Steps

1. **Custom Domain**: Add Route53 domain and SSL certificate
2. **Monitoring**: Set up CloudWatch alarms
3. **Scaling**: Increase task counts for HA
4. **Backups**: Enable RDS automated backups
5. **Security**: Review security groups and IAM policies

## Support

- Check `deployment/README.md` for detailed documentation
- View logs: `aws logs tail /aws/ecs/backend --follow`
- Describe services: `aws ecs describe-services --cluster <cluster> --services <service>`
