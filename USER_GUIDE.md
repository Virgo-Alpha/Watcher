# Watcher User Guide

## Getting Started

### 1. Sign Up (Create Account)

**API Endpoint:** `POST /api/v1/auth/register/`

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "username": "your-username",
    "password": "YourSecurePassword123!",
    "password_confirm": "YourSecurePassword123!",
    "first_name": "Your",
    "last_name": "Name"
  }'
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "email": "your-email@example.com",
    "username": "your-username",
    "first_name": "Your",
    "last_name": "Name"
  },
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Password Requirements:**
- At least 8 characters
- Cannot be too common (e.g., "password123")
- Cannot be entirely numeric

### 2. Login

**API Endpoint:** `POST /api/v1/auth/login/`

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "password": "YourSecurePassword123!"
  }'
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "email": "your-email@example.com",
    "username": "your-username"
  },
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

Save the `access` token - you'll need it for all authenticated requests.

---

## Managing Haunts (Website Monitors)

### 3. Create a Haunt

**API Endpoint:** `POST /api/v1/haunts/`

```bash
curl -X POST http://localhost:8000/api/v1/haunts/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "GitHub Status",
    "url": "https://www.githubstatus.com/",
    "description": "Monitor GitHub service status - alert me when there are incidents",
    "scrape_interval": 15,
    "is_public": false
  }'
```

**Parameters:**
- `name` (required): Display name for your haunt
- `url` (required): Website URL to monitor
- `description` (required): Natural language description of what to monitor
- `scrape_interval` (optional): How often to check (15, 30, 60, or 1440 minutes)
- `is_public` (optional): Make haunt publicly visible (default: false)
- `folder` (optional): Folder ID to organize haunt

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "GitHub Status",
  "url": "https://www.githubstatus.com/",
  "description": "Monitor GitHub service status...",
  "config": {
    "selectors": {
      "status": ".page-status",
      "incidents": ".unresolved-incidents"
    },
    "normalization": {...},
    "alert_on": {...}
  },
  "scrape_interval": 15,
  "is_active": true,
  "is_public": false,
  "created_at": "2025-12-05T15:00:00Z"
}
```

The AI automatically generates the `config` with CSS selectors based on your description!

### 4. List Your Haunts

```bash
curl -X GET http://localhost:8000/api/v1/haunts/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 5. Get Haunt Details

```bash
curl -X GET http://localhost:8000/api/v1/haunts/{haunt_id}/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 6. Update a Haunt

```bash
curl -X PATCH http://localhost:8000/api/v1/haunts/{haunt_id}/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Updated Name",
    "scrape_interval": 30
  }'
```

### 7. Delete a Haunt

```bash
curl -X DELETE http://localhost:8000/api/v1/haunts/{haunt_id}/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Scraping Your Sites

### 8. Manual Scrape (Immediate)

**API Endpoint:** `POST /api/v1/haunts/{haunt_id}/scrape/`

```bash
curl -X POST http://localhost:8000/api/v1/haunts/{haunt_id}/scrape/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "status": "success",
  "message": "Scrape task queued",
  "task_id": "abc123...",
  "haunt_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

This triggers an immediate scrape in the background. The scrape happens asynchronously via Celery.

### 9. Scrape All Your Haunts

To scrape all your haunts at once, you can use a simple script:

```bash
# Get all haunt IDs
curl -X GET http://localhost:8000/api/v1/haunts/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  | jq -r '.results[].id' \
  | while read haunt_id; do
      echo "Scraping haunt: $haunt_id"
      curl -X POST "http://localhost:8000/api/v1/haunts/$haunt_id/scrape/" \
        -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
    done
```

### 10. Check Scrape Status

After triggering a scrape, check the haunt details to see results:

```bash
curl -X GET http://localhost:8000/api/v1/haunts/{haunt_id}/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Look for:
- `last_scraped_at`: When it was last scraped
- `current_state`: Current extracted values
- `error_count`: Number of consecutive errors (0 = healthy)

---

## Viewing Changes (RSS Items)

### 11. Get RSS Items for a Haunt

```bash
curl -X GET http://localhost:8000/api/v1/haunts/{haunt_id}/rss-items/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "count": 5,
  "results": [
    {
      "id": "abc123",
      "title": "Status Changed",
      "ai_summary": "GitHub services are now operational",
      "change_data": {
        "status": {
          "old": "degraded",
          "new": "operational"
        }
      },
      "pub_date": "2025-12-05T14:30:00Z"
    }
  ]
}
```

### 12. Get RSS Feed (XML)

```bash
curl -X GET http://localhost:8000/rss/private/{haunt_id}/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Returns standard RSS 2.0 XML feed that you can use in any RSS reader.

---

## Organizing with Folders

### 13. Create a Folder

```bash
curl -X POST http://localhost:8000/api/v1/folders/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Work",
    "parent": null
  }'
```

### 14. Move Haunt to Folder

```bash
curl -X PATCH http://localhost:8000/api/v1/haunts/{haunt_id}/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "folder": "{folder_id}"
  }'
```

---

## Email Notifications

### 15. Enable/Disable Email Notifications

**User-level (all haunts):**
```bash
curl -X PATCH http://localhost:8000/api/v1/auth/profile/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "email_notifications_enabled": true
  }'
```

**Per-subscription (for public haunts you subscribe to):**
```bash
curl -X PATCH http://localhost:8000/api/v1/subscriptions/{subscription_id}/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "notifications_enabled": false
  }'
```

---

## Frontend Usage (React App)

### Starting the Frontend

```bash
# Development mode
docker-compose up frontend

# Or if running locally
cd frontend
npm install
npm start
```

Access at: `http://localhost:3000`

### Frontend Features

1. **Sign Up Page**: `/signup` or `/register`
   - Fill in email, username, password
   - Automatically logs you in after signup

2. **Login Page**: `/login`
   - Enter email and password
   - Stores JWT token in localStorage

3. **Dashboard**: `/` (after login)
   - Three-panel Google Reader layout
   - Left: Folders and haunts
   - Middle: RSS items list
   - Right: Item details

4. **Create Haunt**: Click "New Haunt" button
   - Enter URL and description
   - AI generates configuration automatically
   - Choose scrape interval

5. **Manual Scrape**: 
   - Click refresh icon next to haunt name
   - Or use "Scrape All" button to scrape all haunts

6. **View Changes**:
   - Click on haunt in left panel
   - RSS items appear in middle panel
   - Click item to see details in right panel

### Keyboard Shortcuts

- `j` / `k`: Navigate items up/down
- `o`: Open selected item
- `s`: Star/unstar item
- `m`: Mark as read/unread
- `r`: Refresh current haunt

---

## Automatic Scraping

Haunts are automatically scraped based on their `scrape_interval`:

- **15 minutes**: Every 15 minutes
- **30 minutes**: Every 30 minutes  
- **60 minutes**: Every hour
- **1440 minutes**: Once per day

Celery Beat scheduler handles this automatically. No manual intervention needed!

---

## Monitoring

### Check Celery Status

```bash
# View Celery worker logs
docker-compose logs -f celery

# View scheduler logs
docker-compose logs -f scheduler

# Check active tasks
docker-compose exec celery celery -A watcher inspect active
```

### Check Scraping Logs

```bash
# View recent scrapes
docker-compose logs -f web | grep "scrape_haunt"

# View email notifications
docker-compose logs -f web | grep "Email notification"
```

---

## Troubleshooting

### Haunt Not Detecting Changes

1. Check the configuration:
```bash
curl -X GET http://localhost:8000/api/v1/haunts/{haunt_id}/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  | jq '.config'
```

2. Manually scrape and check for errors:
```bash
curl -X POST http://localhost:8000/api/v1/haunts/{haunt_id}/scrape/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

3. Check error count:
```bash
curl -X GET http://localhost:8000/api/v1/haunts/{haunt_id}/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  | jq '.error_count, .last_error'
```

### Fix Broken Selectors

For demo haunts specifically:
```bash
docker-compose exec web python backend/scripts/fix_demo_haunts.py
```

For all haunts (general command):
```bash
docker-compose exec web python manage.py fix_all_haunts
```

### Not Receiving Emails

1. Check user preferences:
```bash
curl -X GET http://localhost:8000/api/v1/auth/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  | jq '.email_notifications_enabled'
```

2. Check email logs:
```bash
docker-compose logs -f web | grep "Email notification"
```

3. In development, emails are printed to console (not actually sent)

---

## API Reference

Full API documentation available at:
- Swagger UI: `http://localhost:8000/api/schema/swagger-ui/`
- ReDoc: `http://localhost:8000/api/schema/redoc/`
- OpenAPI JSON: `http://localhost:8000/api/schema/`

---

## Quick Start Script

Here's a complete example to get started:

```bash
#!/bin/bash

# 1. Sign up
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }')

# Extract access token
TOKEN=$(echo $RESPONSE | jq -r '.access')
echo "Access Token: $TOKEN"

# 2. Create a haunt
HAUNT=$(curl -s -X POST http://localhost:8000/api/v1/haunts/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "GitHub Status",
    "url": "https://www.githubstatus.com/",
    "description": "Alert me when GitHub has service issues",
    "scrape_interval": 15
  }')

HAUNT_ID=$(echo $HAUNT | jq -r '.id')
echo "Created Haunt ID: $HAUNT_ID"

# 3. Trigger immediate scrape
curl -X POST "http://localhost:8000/api/v1/haunts/$HAUNT_ID/scrape/" \
  -H "Authorization: Bearer $TOKEN"

echo "Scrape triggered! Check back in a few seconds."

# 4. Check results
sleep 5
curl -X GET "http://localhost:8000/api/v1/haunts/$HAUNT_ID/" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.current_state, .last_scraped_at'
```

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f web`
2. Review documentation in `/docs` folder
3. Check test files for usage examples
