# Subscription Services Test Coverage

## Overview

Comprehensive unit tests for the subscription service business logic, with special focus on the query optimization change from `union()` to `Q()` with `distinct()` in the `get_unread_counts_for_user` method.

## Test Files

- `test_services.py` - Service layer business logic tests (24 tests)
- `test_subscription_api.py` - API endpoint tests (existing)
- `test_read_state.py` - Read state model tests (existing)

## Test Coverage Summary

### SubscriptionService Tests (8 tests)

Tests for core subscription functionality:

1. **test_subscribe_to_public_haunt** - Verifies users can subscribe to public haunts
2. **test_cannot_subscribe_to_private_haunt** - Ensures private haunts cannot be subscribed to
3. **test_cannot_subscribe_to_own_haunt** - Prevents self-subscription
4. **test_unsubscribe_from_haunt** - Tests unsubscription functionality
5. **test_is_subscribed** - Checks subscription status
6. **test_get_unread_count_for_haunt_no_items** - Handles haunts with no RSS items
7. **test_get_unread_count_for_haunt_with_items** - Counts unread items correctly
8. **test_get_unread_count_for_haunt_with_items** - Tests read/unread state tracking

### GetUnreadCountsForUser Tests (10 tests)

Focused tests for the optimized `get_unread_counts_for_user` method:

1. **test_get_unread_counts_no_items** - Returns zero counts when no RSS items exist
2. **test_get_unread_counts_with_unread_items** - Correctly counts unread items across haunts
3. **test_get_unread_counts_with_read_items** - Excludes read items from counts
4. **test_get_unread_counts_includes_owned_and_subscribed** - Includes both owned and subscribed haunts
5. **test_get_unread_counts_no_duplicate_haunts** - Verifies `distinct()` prevents duplicates
6. **test_get_unread_counts_folder_aggregation** - Aggregates haunt counts into folder counts
7. **test_get_unread_counts_empty_folders** - Handles folders with no haunts
8. **test_get_unread_counts_haunts_without_folder** - Counts haunts not in folders
9. **test_get_unread_counts_user_isolation** - Ensures user-specific read states
10. **test_get_unread_counts_performance_single_query** - Validates query optimization

### ReadStateService Tests (6 tests)

Tests for read/starred state management:

1. **test_mark_as_read** - Marks items as read
2. **test_mark_as_unread** - Marks items as unread
3. **test_toggle_starred** - Toggles starred state
4. **test_get_read_state_exists** - Retrieves existing read state
5. **test_get_read_state_not_exists** - Handles non-existent read state
6. **test_get_starred_items** - Filters starred items
7. **test_get_unread_items** - Filters unread items

## Key Test Scenarios

### Query Optimization Testing

The change from `union()` to `Q()` with `distinct()` is specifically tested in:

- **test_get_unread_counts_no_duplicate_haunts**: Ensures no duplicate haunts in results
- **test_get_unread_counts_performance_single_query**: Validates efficient query execution
- **test_get_unread_counts_includes_owned_and_subscribed**: Tests the Q() logic for combining owned and subscribed haunts

### Edge Cases Covered

- Empty folders
- Haunts without folders
- No RSS items
- All items read
- Mixed read/unread states
- User isolation (read states are per-user)
- Public vs private haunts
- Self-subscription prevention

## Code Change Context

### Original Implementation
```python
owned_haunts = Haunt.objects.filter(owner=user)
subscribed_haunts = Haunt.objects.filter(subscriptions__user=user)
all_haunts = owned_haunts.union(subscribed_haunts)
```

### Optimized Implementation
```python
from django.db.models import Q

all_haunts = Haunt.objects.filter(
    Q(owner=user) | Q(subscriptions__user=user)
).distinct()
```

### Benefits of the Change

1. **Single Query**: Uses one query instead of two separate queries + union
2. **Better Performance**: `Q()` with `distinct()` is more efficient than `union()`
3. **Cleaner Code**: More Pythonic and easier to read
4. **Proper Deduplication**: `distinct()` ensures no duplicate haunts

## Test Execution

All 24 tests pass successfully:

```bash
docker-compose exec web python manage.py test apps.subscriptions.tests.test_services
```

**Result**: ✅ Ran 24 tests in 17.266s - OK

## Test Data Patterns

Tests use realistic data structures:

- **Users**: Multiple users for isolation testing
- **Folders**: Hierarchical organization
- **Haunts**: Mix of owned, subscribed, public, and private
- **RSS Items**: Proper field structure (title, description, link, guid, pub_date)
- **Read States**: User-specific read/starred tracking

## Future Test Considerations

Potential areas for additional testing:

1. Performance testing with large datasets (1000+ haunts)
2. Concurrent read state updates
3. Bulk operations testing
4. Cache invalidation scenarios
5. Database query count optimization verification
