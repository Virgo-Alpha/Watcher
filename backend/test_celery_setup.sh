#!/bin/bash
# Script to verify Celery setup in Docker environment

echo "=== Celery Setup Verification ==="
echo ""

echo "1. Starting Docker services..."
docker-compose up -d db redis

echo ""
echo "2. Waiting for services to be ready..."
sleep 5

echo ""
echo "3. Running Django migrations..."
docker-compose run --rm web python manage.py migrate

echo ""
echo "4. Testing Celery worker connection..."
docker-compose run --rm celery celery -A watcher inspect ping

echo ""
echo "5. Testing Celery beat scheduler..."
docker-compose run --rm scheduler celery -A watcher beat --loglevel=info --max-interval=5 &
BEAT_PID=$!
sleep 10
kill $BEAT_PID

echo ""
echo "6. Running Celery task tests..."
docker-compose run --rm web python manage.py test apps.scraping.tests.test_celery_tasks

echo ""
echo "7. Cleaning up..."
docker-compose down

echo ""
echo "=== Verification Complete ==="
