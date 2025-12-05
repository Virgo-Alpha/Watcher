# 🚀 Deploy Watcher to AWS - RIGHT NOW

## You're Ready! ✅

All prerequisites checked and passed. Let's deploy.

## Single Command Deployment

```bash
cd deployment
bash fast-deploy.sh
```

## What Happens Next

```
⏱️  Time: 20-30 minutes total

📦 Installing CDK dependencies... (1 min)
🔧 Bootstrapping AWS CDK... (1 min)
🏗️  Deploying infrastructure... (10-15 min)
   ├─ VPC with subnets
   ├─ RDS PostgreSQL
   ├─ ElastiCache Redis
   ├─ ECS Cluster
   ├─ Application Load Balancer
   └─ CloudFront Distribution

🐳 Building Docker images... (5-8 min)
   ├─ Backend (Django)
   └─ Frontend (React)

📤 Pushing to ECR... (2-3 min)

🔄 Deploying to ECS... (3-5 min)
   ├─ Backend service
   ├─ Frontend service
   ├─ Celery worker
   └─ Celery beat

🗄️  Running migrations... (2-3 min)
📊 Populating demo data... (1 min)

🎉 DONE!
```

## After Deployment

You'll see:

```
🌐 CloudFront URL: https://d1234567890.cloudfront.net
🔗 ALB URL: http://watcher-alb-xxx.elb.amazonaws.com

🔑 Demo Login:
   Email: demo@watcher.local
   Password: demo123
```

**Use ALB URL immediately** (CloudFront takes 10-15 min to propagate)

## What You Get

✅ Production-ready infrastructure
✅ 4 ECS Fargate services running
✅ PostgreSQL database with migrations
✅ Redis for caching and tasks
✅ 6 public haunts pre-configured
✅ Demo user with sample data
✅ CloudFront CDN for global access

## Cost

**~$110/month** for all AWS resources

## Quick Commands

```bash
# Check status
bash status.sh

# View logs
bash logs.sh backend

# Rebuild
bash build-and-push.sh

# Destroy
bash destroy.sh
```

## Ready?

```bash
cd deployment
bash fast-deploy.sh
```

**Go! 🚀**
