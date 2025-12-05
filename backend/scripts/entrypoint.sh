#!/bin/bash
# Entrypoint script for Django container
# Handles database migrations and initial data population

set -e

echo "=========================================="
echo "Watcher Backend Initialization"
echo "=========================================="

# Wait for database to be ready
echo "⏳ Waiting for database..."
while ! pg_isready -h db -p 5432 -U postgres > /dev/null 2>&1; do
    sleep 1
done
echo "✅ Database is ready"

# Run migrations
echo ""
echo "🔄 Running database migrations..."
python manage.py migrate --noinput

# Check if public haunts exist
echo ""
echo "📚 Checking for public haunts..."
PUBLIC_HAUNTS_COUNT=$(python manage.py shell -c "from apps.haunts.models import Haunt; from django.contrib.auth import get_user_model; User = get_user_model(); system_user = User.objects.filter(email='system@watcher.local').first(); print(Haunt.objects.filter(owner=system_user, is_public=True).count() if system_user else 0)" 2>/dev/null || echo "0")

if [ "$PUBLIC_HAUNTS_COUNT" = "0" ]; then
    echo "📥 Populating public haunts (first-time setup)..."
    python manage.py populate_public_haunts
    echo "✅ Public haunts populated successfully"
else
    echo "✅ Public haunts already exist (count: $PUBLIC_HAUNTS_COUNT)"
fi

# Collect static files in production
if [ "$DEBUG" = "False" ]; then
    echo ""
    echo "📦 Collecting static files..."
    python manage.py collectstatic --noinput
fi

echo ""
echo "=========================================="
echo "✅ Initialization Complete"
echo "=========================================="
echo ""

# Execute the main command
exec "$@"
