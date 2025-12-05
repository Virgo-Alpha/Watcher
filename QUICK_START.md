# Quick Start Guide

## ✅ User Signup - Already Working!

User signup functionality exists and all tests pass (16/16 ✅).

### Sign Up via API

```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "username": "your-username",
    "password": "YourSecurePassword123!",
    "password_confirm": "YourSecurePassword123!"
  }'
```

**Returns:** User info + JWT tokens (access & refresh)

---

## 🔍 How to Scrape All Your Sites

### Option 1: From Frontend (React App)

1. **Start the frontend:**
   ```bash
   docker-compose up frontend
   # Access at http://localhost:3000
   ```

2. **Login** at `/login`

3. **Click "Scrape All" button** in the UI
   - Located in the top toolbar
   - Triggers scraping for all your haunts at once

4. **Or scrape individual haunts:**
   - Click the refresh icon (↻) next to any haunt name
   - Triggers immediate scrape for that haunt

### Option 2: Via API (Manual Scrape)

**Scrape a single haunt:**
```bash
curl -X POST http://localhost:8000/api/v1/haunts/{haunt_id}/scrape/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Scrape all your haunts (bash script):**
```bash
# Get your access token first (from login response)
TOKEN="your_access_token_here"

# Scrape all haunts
curl -X GET http://localhost:8000/api/v1/haunts/ \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.results[].id' \
  | while read haunt_id; do
      echo "Scraping: $haunt_id"
      curl -X POST "http://localhost:8000/api/v1/haunts/$haunt_id/scrape/" \
        -H "Authorization: Bearer $TOKEN"
      sleep 1  # Be nice to the server
    done
```

### Option 3: Automatic Scraping (Recommended)

Haunts are **automatically scraped** based on their `scrape_interval`:

- Every 15 minutes
- Every 30 minutes
- Every hour
- Once per day

**No manual action needed!** Celery Beat handles this automatically.

To check if automatic scraping is working:
```bash
# Check scheduler logs
docker-compose logs -f scheduler

# Check worker logs
docker-compose logs -f celery
```

---

## 📊 View Scraping Results

### Via API

```bash
# Get haunt details (includes current_state)
curl -X GET http://localhost:8000/api/v1/haunts/{haunt_id}/ \
  -H "Authorization: Bearer $TOKEN"

# Get RSS items (detected changes)
curl -X GET http://localhost:8000/api/v1/haunts/{haunt_id}/rss-items/ \
  -H "Authorization: Bearer $TOKEN"
```

### Via Frontend

1. Click on a haunt in the left panel
2. RSS items appear in the middle panel
3. Click an item to see details in the right panel

---

## 🎯 Complete Workflow Example

```bash
#!/bin/bash

# 1. Sign up
SIGNUP=$(curl -s -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@example.com",
    "username": "demouser",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }')

TOKEN=$(echo $SIGNUP | jq -r '.access')
echo "✅ Signed up! Token: ${TOKEN:0:20}..."

# 2. Create a haunt
HAUNT=$(curl -s -X POST http://localhost:8000/api/v1/haunts/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "GitHub Status",
    "url": "https://www.githubstatus.com/",
    "description": "Alert me when GitHub has incidents",
    "scrape_interval": 15
  }')

HAUNT_ID=$(echo $HAUNT | jq -r '.id')
echo "✅ Created haunt: $HAUNT_ID"

# 3. Scrape immediately
curl -s -X POST "http://localhost:8000/api/v1/haunts/$HAUNT_ID/scrape/" \
  -H "Authorization: Bearer $TOKEN" > /dev/null

echo "✅ Scrape triggered!"
echo "⏳ Waiting 5 seconds for scrape to complete..."
sleep 5

# 4. Check results
echo "📊 Current state:"
curl -s -X GET "http://localhost:8000/api/v1/haunts/$HAUNT_ID/" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{
      name: .name,
      last_scraped: .last_scraped_at,
      current_state: .current_state,
      error_count: .error_count
    }'

echo ""
echo "✅ Done! Your haunt will now be scraped automatically every 15 minutes."
```

---

## 🚀 Frontend Quick Start

### 1. Access the App

```bash
# Make sure services are running
docker-compose up -d

# Frontend available at:
http://localhost:3000
```

### 2. Sign Up

- Go to `/signup` or `/register`
- Fill in: email, username, password
- Automatically logs you in

### 3. Create Your First Haunt

- Click "New Haunt" button
- Enter:
  - **Name**: "GitHub Status"
  - **URL**: "https://www.githubstatus.com/"
  - **Description**: "Alert me when GitHub has service issues"
  - **Interval**: 15 minutes
- Click "Create"

### 4. Scrape It

- Click the refresh icon (↻) next to your haunt
- Or click "Scrape All" to scrape all haunts
- Wait a few seconds
- Changes appear in the middle panel

### 5. View Changes

- Click on your haunt in the left panel
- RSS items (changes) appear in middle panel
- Click an item to see full details

---

## 📧 Email Notifications

You'll automatically receive emails when changes are detected!

**To disable:**
```bash
curl -X PATCH http://localhost:8000/api/v1/auth/profile/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"email_notifications_enabled": false}'
```

---

## 🔧 Troubleshooting

### Haunt not scraping?

```bash
# Check if it's active
curl -X GET http://localhost:8000/api/v1/haunts/{haunt_id}/ \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.is_active, .error_count, .last_error'

# Check Celery workers
docker-compose logs -f celery
```

### No changes detected?

```bash
# Fix demo haunt selectors (for demo data)
docker-compose exec web python backend/scripts/fix_demo_haunts.py

# Fix all haunt selectors (general command)
docker-compose exec web python manage.py fix_all_haunts

# Or manually scrape to see errors
curl -X POST http://localhost:8000/api/v1/haunts/{haunt_id}/scrape/ \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📚 Full Documentation

- **USER_GUIDE.md** - Complete API reference
- **EMAIL_NOTIFICATIONS_IMPLEMENTATION.md** - Email system docs
- **HAUNT_SELECTOR_FIX.md** - Selector troubleshooting
- **API Docs**: http://localhost:8000/api/schema/swagger-ui/

---

## ✨ Key Features

✅ **User signup & authentication** (JWT tokens)
✅ **AI-powered haunt configuration** (natural language → CSS selectors)
✅ **Manual scraping** (immediate, on-demand)
✅ **Automatic scraping** (scheduled via Celery Beat)
✅ **Email notifications** (when changes detected)
✅ **RSS feeds** (standard RSS 2.0 XML)
✅ **Google Reader UI** (three-panel layout)
✅ **Folder organization** (group related haunts)
✅ **Public/private haunts** (share with community)
✅ **Keyboard shortcuts** (j/k navigation, etc.)

---

## 🎉 You're All Set!

Your Watcher instance is ready to monitor websites. Happy haunting! 👻
