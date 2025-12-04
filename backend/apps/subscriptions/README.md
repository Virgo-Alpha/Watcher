# Subscription Management Module

This module implements subscription management and read state tracking for the Watcher application.

## Features Implemented

### 1. Subscription API Endpoints (Task 8.1)

**Endpoints:**
- `POST /api/v1/subscriptions/` - Create a new subscription to a public haunt
- `GET /api/v1/subscriptions/` - List user's subscriptions
- `GET /api/v1/subscriptions/{id}/` - Get subscription details
- `PATCH /api/v1/subscriptions/{id}/` - Update subscription (e.g., toggle notifications)
- `DELETE /api/v1/subscriptions/{id}/` - Unsubscribe from a haunt
- `POST /api/v1/subscriptions/unsubscribe_by_haunt/` - Unsubscribe by haunt ID
- `GET /api/v1/subscriptions/check_subscription/` - Check if subscribed to a haunt
- `GET /api/v1/subscriptions/unread_counts/` - Get unread counts for all haunts and folders
- `GET /api/v1/subscriptions/navigation/` - Get navigation data with subscribed haunts

**Features:**
- Users can subscribe to public haunts created by others
- Cannot subscribe to private haunts
- Cannot subscribe to own haunts
- Subscription status checking utilities
- Unread count aggregation for haunts and folders

### 2. Enhanced Read State Tracking (Task 8.2)

**Endpoints:**
- `POST /api/v1/read-states/mark_read/` - Mark a single item as read
- `POST /api/v1/read-states/mark_unread/` - Mark a single item as unread
- `POST /api/v1/read-states/toggle_starred/` - Toggle starred state
- `POST /api/v1/read-states/bulk_mark_read/` - Bulk mark multiple items as read/unread
- `GET /api/v1/read-states/starred_items/` - Get all starred items
- `GET /api/v1/read-states/unread_items/` - Get all unread items
- `GET /api/v1/read-states/` - List read states with filtering

**Features:**
- Individual and bulk read/unread operations
- Star/unstar functionality with keyboard shortcut support
- Auto-mark-as-read support (API ready for frontend implementation)
- Unread count aggregation for folders and haunts
- Efficient bulk operations to minimize database queries

### 3. Subscription-Aware Navigation API (Task 8.3)

**Endpoint:**
- `GET /api/v1/subscriptions/navigation/` - Get navigation tree with subscribed haunts

**Features:**
- Returns folder tree with nested structure
- Includes both owned and subscribed haunts
- Provides unread counts for each folder and haunt
- Organizes haunts by folder
- Supports filtering (include/exclude owned haunts)

**UI Preferences API:**
- `GET /api/v1/preferences/` - Get user UI preferences
- `PUT /api/v1/preferences/` - Update UI preferences
- `PATCH /api/v1/preferences/` - Partial update UI preferences
- `POST /api/v1/preferences/toggle_folder_collapsed/` - Toggle folder collapsed state

### 4. Manual Refresh and Scraping (Task 8.4)

**Endpoints:**
- `POST /api/v1/haunts/{id}/refresh/` - Manually trigger immediate scrape
- `GET /api/v1/haunts/{id}/scrape_status/` - Get scraping status

**Features:**
- Manual scrape trigger for individual haunts
- Rate limiting (max 1 refresh per 5 minutes per haunt)
- Real-time status updates for ongoing scrape operations
- Returns task ID for tracking
- Scrape status endpoint with next scheduled scrape time

## Services

### SubscriptionService

Business logic for subscription management:
- `get_user_subscriptions(user)` - Get all subscriptions for a user
- `subscribe_to_haunt(user, haunt, notifications_enabled)` - Subscribe to a haunt
- `unsubscribe_from_haunt(user, haunt)` - Unsubscribe from a haunt
- `is_subscribed(user, haunt)` - Check subscription status
- `get_unread_count_for_haunt(user, haunt)` - Get unread count for a haunt
- `get_unread_counts_for_user(user)` - Get all unread counts for a user

### ReadStateService

Business logic for read state management:
- `mark_as_read(user, rss_item)` - Mark item as read
- `mark_as_unread(user, rss_item)` - Mark item as unread
- `toggle_starred(user, rss_item)` - Toggle starred state
- `bulk_mark_read(user, rss_items)` - Bulk mark items as read
- `get_read_state(user, rss_item)` - Get read state for an item
- `get_starred_items(user, haunt)` - Get starred items
- `get_unread_items(user, haunt)` - Get unread items

## Models

### Subscription
- Links users to public haunts they're subscribed to
- Tracks subscription date and notification preferences
- Validates that haunts are public and prevents self-subscription

### UserReadState
- Tracks read/starred state per user per RSS item
- Includes timestamps for read_at and starred_at
- Provides helper methods for state management
- Supports bulk operations for efficiency

## Tests

### test_subscription_api.py
- Test subscribing to public haunts
- Test preventing subscription to private haunts
- Test preventing self-subscription
- Test listing subscriptions
- Test unsubscribing
- Test checking subscription status

### test_read_state.py
- Test marking items as read/unread
- Test toggling starred state
- Test bulk marking items as read
- Test getting starred items
- Test getting unread items

## Integration

The subscription module integrates with:
- **Haunts app**: For haunt data and folder organization
- **RSS app**: For RSS item data
- **Authentication app**: For user management
- **Scraping app**: For manual refresh functionality

## Usage Examples

### Subscribe to a public haunt
```python
POST /api/v1/subscriptions/
{
    "haunt_id": "uuid-here",
    "notifications_enabled": true
}
```

### Mark multiple items as read
```python
POST /api/v1/read-states/bulk_mark_read/
{
    "rss_item_ids": ["uuid1", "uuid2", "uuid3"],
    "is_read": true
}
```

### Get navigation with unread counts
```python
GET /api/v1/subscriptions/navigation/?include_owned=true
```

### Manually refresh a haunt
```python
POST /api/v1/haunts/{haunt_id}/refresh/
```

## Requirements Validated

This implementation satisfies the following requirements from the design document:

- **Requirement 9.1**: Users can subscribe to public haunts
- **Requirement 9.2**: Subscribed haunts appear in navigation
- **Requirement 9.3**: Users can track read/unread state and star items
- **Requirement 17.1**: Auto-mark-as-read when items are opened (API ready)
- **Requirement 17.2**: Auto-mark-as-read when scrolled past (API ready)
- **Requirement 17.5**: Toggle read/unread with keyboard shortcuts (API ready)
- **Requirement 17.6**: Toggle starred with keyboard shortcuts (API ready)
- **Requirement 17.7**: Manual refresh functionality with rate limiting
- **Requirement 13.4**: Unread count badges for folders and haunts
