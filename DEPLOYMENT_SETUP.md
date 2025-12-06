# Local vs Production Configuration Setup

## Summary

This document explains the separation between local development and production configurations to ensure your local setup works independently from AWS deployments.

## Problem

Previously, the project used a single Docker configuration that mixed development and production concerns:
- Frontend used production `Dockerfile` (nginx + static build) even for local development
- No hot reload for React development
- Migrations ran on all containers causing race conditions
- Local and production weren't clearly separated

## Solution

Created two distinct Docker Compose configurations:

### 1. Local Development (`docker-compose.yml`)

**Purpose**: Fast iteration during development

**Configuration**:
- Frontend uses `Dockerfile.dev` with React dev server
- Hot reload enabled via volume mounts
- Debug mode enabled
- Migrations only run on web container (not celery/beat)
- Ports: Frontend 3000, Backend 8000, DB 5432, Redis 6379

**Usage**:
```bash
# Start development environment
docker-compose up -d

# Setup demo data
docker-compose exec web python manage.py populate_demo_data

# Access
# Frontend: http://localhost:3000
# Backend: http://localhost:8000/api/v1
```

### 2. Production (`docker-compose.prod.yml` + AWS)

**Purpose**: Production-ready builds for testing and deployment

**Configuration**:
- Frontend uses production `Dockerfile` with nginx serving optimized static build
- No volume mounts (code baked into images)
- Debug mode disabled
- Production Django settings
- Ports: Frontend 80, Backend 8000, DB 5433, Redis 6380

**Local Testing**:
```bash
# Test production build locally
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml exec web python manage.py populate_demo_data

# Access at http://localhost (port 80)
```

**AWS Deployment**:
- Uses same production Dockerfile
- Deployed via CDK to ECS Fargate
- CloudFront CDN for global access
- RDS PostgreSQL and ElastiCache Redis

## Key Changes Made

### 1. Fixed `docker-compose.yml`
- Changed frontend to use `Dockerfile.dev` instead of `Dockerfile`
- Enables hot reload for React development

### 2. Created `docker-compose.prod.yml`
- New file for production-like local testing
- Uses production Dockerfiles
- Different ports to avoid conflicts with dev setup
- Separate volumes (`postgres_data_prod`, `redis_data_prod`)

### 3. Updated `backend/scripts/entrypoint.sh`
- Made executable: `chmod +x backend/scripts/entrypoint.sh`
- Added logic to only run migrations on web container
- Prevents race conditions when celery/beat containers try to migrate simultaneously
- Checks if command contains "runserver" or "gunicorn"

### 4. Updated Documentation

**README.md**:
- Added clear explanation of local vs production configs
- Simplified quick start (migrations now automatic)
- Added "Why Two Configurations?" section

**deployment/README.md**:
- Added local vs production comparison at top
- Added testing production build locally section
- Added AWS deployment verification steps

## File Structure

```
watcher/
├── docker-compose.yml              # Local development (hot reload)
├── docker-compose.prod.yml         # Production testing (optimized build)
├── backend/
│   ├── Dockerfile                  # Production backend (gunicorn)
│   └── scripts/
│       └── entrypoint.sh          # Smart migration logic
├── frontend/
│   ├── Dockerfile                  # Production frontend (nginx)
│   └── Dockerfile.dev             # Development frontend (dev server)
└── deployment/
    ├── cdk/                       # AWS infrastructure
    └── deploy.sh                  # AWS deployment script
```

## Testing Checklist

### Local Development
- [x] `docker-compose up -d` starts all services
- [x] Frontend accessible at http://localhost:3000
- [x] Backend API at http://localhost:8000/api/v1
- [x] Hot reload works (edit React file, see changes)
- [x] Demo user login works
- [x] All containers running (web, frontend, db, redis, celery, scheduler)

### Production Local Test
- [x] `docker-compose -f docker-compose.prod.yml up -d` starts services
- [x] Frontend at http://localhost (port 80)
- [x] Backend API at http://localhost:8000/api/v1
- [x] Static files served by nginx
- [x] Gunicorn running (not runserver)
- [x] Demo user login works

### AWS Deployment
- [x] CloudFront URL accessible
- [x] Frontend loads correctly
- [x] Backend API responds
- [x] Demo user login works
- [x] All ECS services running (4 services)

## Benefits

1. **No More Confusion**: Clear separation between dev and prod
2. **Faster Development**: Hot reload works out of the box
3. **Safer Deployments**: Test production build locally first
4. **No Race Conditions**: Migrations only run once
5. **Fork-Friendly**: Anyone cloning the repo gets working local setup

## Commands Reference

### Local Development
```bash
# Start
docker-compose up -d

# Setup
docker-compose exec web python manage.py populate_demo_data

# Logs
docker-compose logs -f web
docker-compose logs -f frontend

# Stop
docker-compose down
```

### Production Testing
```bash
# Start
docker-compose -f docker-compose.prod.yml up -d

# Setup
docker-compose -f docker-compose.prod.yml exec web python manage.py populate_demo_data

# Logs
docker-compose -f docker-compose.prod.yml logs -f web

# Stop
docker-compose -f docker-compose.prod.yml down
```

### AWS Deployment
```bash
cd deployment

# Deploy
./deploy.sh

# Update
./update.sh

# Status
./status.sh

# Logs
./logs.sh BackendService

# Destroy
./destroy.sh
```

## Troubleshooting

### Local dev frontend not updating
- Make sure you're using `docker-compose.yml` (not prod)
- Check that `Dockerfile.dev` is being used
- Restart frontend: `docker-compose restart frontend`

### Migrations failing
- Check entrypoint.sh has execute permissions: `ls -la backend/scripts/entrypoint.sh`
- Should show `-rwxr-xr-x` (executable)
- If not: `chmod +x backend/scripts/entrypoint.sh`

### Port conflicts
- Local dev uses: 3000, 8000, 5432, 6379
- Production test uses: 80, 8000, 5433, 6380
- Stop one before starting the other

### AWS deployment issues
- Check `deployment/cdk-outputs.json` exists
- Verify ECS services are running: `./status.sh`
- Check logs: `./logs.sh BackendService`
