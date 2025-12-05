# Test Summary: HauntListSerializer Subscription Fields

## Overview
Added comprehensive unit tests for the new `is_subscribed` and `owner_email` fields in `HauntListSerializer`.

## Changes to Serializer (backend/apps/haunts/serializers.py)
- Added `is_subscribed` field: Checks if the current user is subscribed to a haunt (returns False if user owns it)
- Added `owner_email` field: Returns the email address of the haunt owner
- Both fields are SerializerMethodFields with custom getter methods

## Test Coverage Added

### Test Class: `HauntListSerializerSubscriptionTestCase`
Location: `backend/apps/haunts/tests/test_serializers.py`

#### Test Cases (16 total):

1. **test_list_serializer_is_subscribed_for_subscriber**
   - Verifies `is_subscribed` returns `True` for users who have subscribed to a haunt

2. **test_list_serializer_is_subscribed_for_owner**
   - Verifies `is_subscribed` returns `False` for haunt owners (owners don't subscribe to their own haunts)

3. **test_list_serializer_is_subscribed_for_non_subscriber**
   - Verifies `is_subscribed` returns `False` for authenticated users who haven't subscribed

4. **test_list_serializer_is_subscribed_unauthenticated**
   - Verifies `is_subscribed` returns `False` for unauthenticated users

5. **test_list_serializer_is_subscribed_no_request**
   - Verifies `is_subscribed` handles missing request context gracefully (returns `False`)

6. **test_list_serializer_owner_email_present**
   - Verifies `owner_email` field is included and contains correct email

7. **test_list_serializer_owner_email_for_own_haunt**
   - Verifies `owner_email` is present even when viewing own haunts

8. **test_list_serializer_owner_email_none_when_no_owner**
   - Verifies `owner_email` returns `None` when haunt has no owner (edge case)

9. **test_list_serializer_multiple_haunts_subscription_status**
   - Verifies subscription status is correctly calculated for multiple haunts in a list

10. **test_list_serializer_subscription_after_unsubscribe**
    - Verifies `is_subscribed` updates to `False` after unsubscribing

11. **test_list_serializer_subscription_after_subscribe**
    - Verifies `is_subscribed` updates to `True` after subscribing

12. **test_list_serializer_mixed_owned_and_subscribed_haunts**
    - Verifies correct behavior when list contains both owned and subscribed haunts

13. **test_list_serializer_subscription_query_efficiency**
    - Tests subscription checking with multiple haunts to ensure correct behavior at scale

14. **test_list_serializer_private_haunt_subscription_fields**
    - Verifies subscription fields work correctly with private haunts

15. **test_list_serializer_fields_consistency_with_detail_serializer**
    - Ensures `is_subscribed` and `owner_email` are consistent between list and detail serializers

16. **test_list_serializer_subscription_with_deleted_user**
    - Verifies serializer handles edge cases gracefully without errors

## Test Setup
- Creates three users: owner, subscriber, and other_user
- Creates public and private haunts
- Creates subscription relationships
- Uses Django's RequestFactory to simulate authenticated requests

## Edge Cases Covered
- Unauthenticated users
- Missing request context
- Haunts with no owner
- Subscription state changes (subscribe/unsubscribe)
- Mixed lists of owned and subscribed haunts
- Private vs public haunts
- Multiple haunts with different subscription states

## Running the Tests

### Using Docker (recommended):
```bash
docker-compose exec web python manage.py test apps.haunts.tests.test_serializers.HauntListSerializerSubscriptionTestCase
```

### Run all serializer tests:
```bash
docker-compose exec web python manage.py test apps.haunts.tests.test_serializers
```

### Run specific test:
```bash
docker-compose exec web python manage.py test apps.haunts.tests.test_serializers.HauntListSerializerSubscriptionTestCase.test_list_serializer_is_subscribed_for_subscriber
```

## Integration Points
These tests verify the integration between:
- `HauntListSerializer` (apps.haunts.serializers)
- `Subscription` model (apps.subscriptions.models)
- Django authentication system
- Request context handling

## Notes
- Tests use Django's TestCase for database transactions
- Each test is isolated with setUp/tearDown
- Tests follow existing project patterns from `HauntSerializerSubscriptionTestCase`
- All tests are designed to be idempotent and independent
