#!/bin/bash
# Script to populate demo and public haunt data

set -e

echo "=========================================="
echo "Watcher Demo Data Setup"
echo "=========================================="
echo ""

# Check if we're in Docker or local environment
if [ -f /.dockerenv ]; then
    PYTHON_CMD="python"
else
    PYTHON_CMD="docker-compose exec web python"
fi

# Populate public haunts
echo "📚 Populating public haunts..."
$PYTHON_CMD manage.py populate_public_haunts

echo ""
echo "=========================================="
echo ""

# Populate demo data
echo "🎭 Populating demo data..."
$PYTHON_CMD manage.py populate_demo_data

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Public haunts are now available to all users."
echo ""
echo "Demo user credentials:"
echo "  Email: demo@watcher.local"
echo "  Password: demo123"
echo ""
echo "To recreate data, run with --recreate flag:"
echo "  $PYTHON_CMD manage.py populate_public_haunts --recreate"
echo "  $PYTHON_CMD manage.py populate_demo_data --recreate"
echo ""
