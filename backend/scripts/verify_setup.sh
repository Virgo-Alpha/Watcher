#!/bin/bash
# Script to verify Watcher setup and data population

set -e

echo "=========================================="
echo "Watcher Setup Verification"
echo "=========================================="
echo ""

# Check if containers are running
echo "1. Checking Docker containers..."
if docker-compose ps | grep -q "Up"; then
    echo "   ✓ Containers are running"
else
    echo "   ✗ Containers are not running"
    echo "   Run: docker-compose up -d"
    exit 1
fi
echo ""

# Check database connection
echo "2. Checking database connection..."
if docker-compose exec -T web python manage.py check --database default > /dev/null 2>&1; then
    echo "   ✓ Database connection successful"
else
    echo "   ✗ Database connection failed"
    exit 1
fi
echo ""

# Check migrations
echo "3. Checking migrations..."
PENDING_MIGRATIONS=$(docker-compose exec -T web python manage.py showmigrations --plan | grep -c "\[ \]" || echo "0")
if [ "$PENDING_MIGRATIONS" = "0" ]; then
    echo "   ✓ All migrations applied"
else
    echo "   ⚠ $PENDING_MIGRATIONS pending migrations"
    echo "   Run: docker-compose exec web python manage.py migrate"
fi
echo ""

# Check AI service
echo "4. Checking AI service..."
AI_STATUS=$(docker-compose exec -T web python manage.py shell -c "from apps.ai.services import AIConfigService; print('available' if AIConfigService().is_available() else 'unavailable')" 2>/dev/null)
if [ "$AI_STATUS" = "available" ]; then
    echo "   ✓ AI service is available"
else
    echo "   ⚠ AI service is unavailable"
    echo "   Set LLM_API_KEY in .env file"
fi
echo ""

# Check public haunts
echo "5. Checking public haunts..."
PUBLIC_COUNT=$(docker-compose exec -T web python manage.py shell -c "from apps.haunts.models import Haunt; from django.contrib.auth import get_user_model; User = get_user_model(); system_user = User.objects.filter(email='system@watcher.local').first(); print(Haunt.objects.filter(owner=system_user, is_public=True).count() if system_user else 0)" 2>/dev/null)
if [ "$PUBLIC_COUNT" -gt "0" ]; then
    echo "   ✓ Public haunts exist ($PUBLIC_COUNT)"
else
    echo "   ⚠ No public haunts found"
    echo "   Run: docker-compose exec web python manage.py populate_public_haunts"
fi
echo ""

# Check demo user
echo "6. Checking demo user..."
DEMO_EXISTS=$(docker-compose exec -T web python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print('yes' if User.objects.filter(email='demo@watcher.local').exists() else 'no')" 2>/dev/null)
if [ "$DEMO_EXISTS" = "yes" ]; then
    DEMO_HAUNTS=$(docker-compose exec -T web python manage.py shell -c "from apps.haunts.models import Haunt; from django.contrib.auth import get_user_model; User = get_user_model(); demo_user = User.objects.get(email='demo@watcher.local'); print(Haunt.objects.filter(owner=demo_user).count())" 2>/dev/null)
    echo "   ✓ Demo user exists with $DEMO_HAUNTS haunts"
    echo "   Credentials: demo@watcher.local / demo123"
else
    echo "   ⚠ Demo user not found"
    echo "   Run: docker-compose exec web python manage.py populate_demo_data"
fi
echo ""

# Check services
echo "7. Checking services..."
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   Django Admin: http://localhost:8000/admin"
echo ""

echo "=========================================="
echo "✅ Setup verification complete!"
echo "=========================================="
