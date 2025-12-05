# 🚀 Deploy Watcher to AWS in 30 Minutes

## One Command Deployment

```bash
cd deployment
bash fast-deploy.sh
```

## What Happens

1. **Infrastructure** (10-15 min): VPC, RDS PostgreSQL, Redis, ECS Cluster, ALB, CloudFront
2. **Build Images** (5-8 min): Backend and Frontend Docker images
3. **Deploy Services** (3-5 min): 4 ECS Fargate services
4. **Setup Data** (2-3 min): Migrations, public haunts, demo user

**Total: ~20-30 minutes**

## After Deployment

You'll get:
- **CloudFront URL**: `https://d1234567890.cloudfront.net` (takes 10-15 min to propagate)
- **ALB URL**: `http://watcher-alb-xxx.elb.amazonaws.com` (immediate access)

Login with:
- Email: `demo@watcher.local`
- Password: `demo123`

## Useful Commands

```bash
# Check deployment status
bash status.sh

# View logs
bash logs.sh backend    # or frontend, celery, beat

# Rebuild and redeploy
bash build-and-push.sh

# Run migrations manually
bash run-migrations.sh

# Destroy everything
bash destroy.sh
```

## Cost

~$110/month for all AWS resources (RDS, Redis, ECS, ALB, NAT Gateway, CloudFront)

## Troubleshooting

**Services not starting?**
```bash
bash status.sh
bash logs.sh backend
```

**Need to re-run setup?**
```bash
bash run-migrations.sh
```

**Want to start over?**
```bash
bash destroy.sh
bash fast-deploy.sh
```

## Files Overview

- `fast-deploy.sh` - Main deployment script
- `status.sh` - Check deployment status
- `logs.sh` - View service logs
- `build-and-push.sh` - Rebuild and push images
- `run-migrations.sh` - Run migrations manually
- `destroy.sh` - Delete all resources
- `cdk/` - AWS CDK infrastructure code

## Next Steps

1. Access your app via the ALB URL
2. Login with demo credentials
3. Explore the 6 pre-configured public haunts
4. Create your own haunts using natural language
5. (Optional) Add custom domain with Route53

## Support

- Full docs: `README.md`
- Quick guide: `QUICKSTART.md`
- AWS CDK code: `cdk/lib/watcher-stack.ts`

---

**Ready? Let's deploy!**

```bash
cd deployment
bash fast-deploy.sh
```
