#!/bin/bash
# Entrypoint script for Django container
# Handles database migrations and initial data population

set -e

echo "=========================================="
echo "Watcher Backend Initialization"
echo "=========================================="

# Note: Skipping database connectivity check
# Django will handle database connection retries automatically
# The health check grace period gives migrations time to complete
echo "⏳ Database connectivity will be checked by Django"

# Only run migrations and setup on the web container
# Celery and beat workers should not run migrations to avoid race conditions
if [[ "$*" == *"runserver"* ]] || [[ "$*" == *"gunicorn"* ]] || [[ "$1" == "python" && "$2" == "manage.py" && "$3" == "runserver" ]]; then
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
else
    echo "⏭️  Skipping migrations (not web container)"
    echo ""
fi

# Execute the main command
exec "$@"
