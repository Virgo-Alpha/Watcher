"""
Tests for haunt serializers.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from apps.subscriptions.models import Subscription
from ..models import Folder, Haunt
from ..serializers import HauntSerializer, HauntListSerializer

User = get_user_model()


class HauntSerializerTestCase(TestCase):
    """Test case for HauntSerializer"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.folder = Folder.objects.create(
            user=self.user,
            name='Test Folder'
        )
        self.haunt = Haunt.objects.create(
            owner=self.user,
            name='Test Haunt',
            url='https://example.com',
            description='Test description',
            folder=self.folder,
            config={
                'selectors': {'status': 'css:.status'},
                'normalization': {'status': {'type': 'text'}},
                'truthy_values': {'status': ['open']}
            }
        )

    def get_serializer_context(self):
        """Create serializer context with request"""
        request = self.factory.get('/')
        request.user = self.user
        return {'request': request}

    def test_haunt_serializer_includes_all_fields(self):
        """Test that HauntSerializer includes all expected fields"""
        context = self.get_serializer_context()
        serializer = HauntSerializer(self.haunt, context=context)
        data = serializer.data

        expected_fields = [
            'id', 'name', 'url', 'description', 'config', 'current_state',
            'last_alert_state', 'alert_mode', 'alert_mode_display',
            'scrape_interval', 'scrape_interval_display', 'is_public',
            'public_slug', 'is_active', 'last_scraped_at', 'last_error',
            'error_count', 'is_healthy', 'folder', 'folder_name',
            'unread_count', 'public_url', 'rss_url', 'created_at', 'updated_at'
        ]

        for field in expected_fields:
            self.assertIn(field, data, f"Field '{field}' missing from serializer")

    def test_haunt_serializer_folder_name(self):
        """Test that folder_name is correctly populated"""
        context = self.get_serializer_context()
        serializer = HauntSerializer(self.haunt, context=context)
        self.assertEqual(serializer.data['folder_name'], 'Test Folder')

    def test_haunt_serializer_folder_name_none(self):
        """Test that folder_name is None when haunt has no folder"""
        haunt_no_folder = Haunt.objects.create(
            owner=self.user,
            name='No Folder Haunt',
            url='https://example.com/nofolder'
        )
        context = self.get_serializer_context()
        serializer = HauntSerializer(haunt_no_folder, context=context)
        self.assertIsNone(serializer.data['folder_name'])

    def test_haunt_serializer_display_fields(self):
        """Test that display fields are included"""
        context = self.get_serializer_context()
        serializer = HauntSerializer(self.haunt, context=context)
        data = serializer.data

        self.assertIn('scrape_interval_display', data)
        self.assertIn('alert_mode_display', data)
        self.assertIsNotNone(data['scrape_interval_display'])
        self.assertIsNotNone(data['alert_mode_display'])

    def test_haunt_serializer_urls(self):
        """Test that public_url and rss_url are generated"""
        context = self.get_serializer_context()
        serializer = HauntSerializer(self.haunt, context=context)
        data = serializer.data

        self.assertIn('public_url', data)
        self.assertIn('rss_url', data)

    def test_haunt_serializer_validate_folder_same_user(self):
        """Test that folder validation requires same user"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_folder = Folder.objects.create(
            user=other_user,
            name='Other Folder'
        )

        context = self.get_serializer_context()
        serializer = HauntSerializer(data={
            'name': 'Invalid Folder Haunt',
            'url': 'https://example.com/invalid',
            'folder': other_folder.id,
            'config': {
                'selectors': {},
                'normalization': {},
                'truthy_values': {}
            }
        }, context=context)

        self.assertFalse(serializer.is_valid())
        self.assertIn('folder', serializer.errors)

    def test_haunt_serializer_validate_config_structure(self):
        """Test that config validation requires all keys"""
        context = self.get_serializer_context()

        # Missing normalization key
        serializer = HauntSerializer(data={
            'name': 'Invalid Config',
            'url': 'https://example.com/invalid',
            'config': {
                'selectors': {},
                'truthy_values': {}
            }
        }, context=context)

        self.assertFalse(serializer.is_valid())
        self.assertIn('config', serializer.errors)

    def test_haunt_serializer_validate_scrape_interval(self):
        """Test that scrape interval validation works"""
        context = self.get_serializer_context()

        serializer = HauntSerializer(data={
            'name': 'Invalid Interval',
            'url': 'https://example.com/invalid',
            'scrape_interval': 999,  # Invalid interval
            'config': {
                'selectors': {},
                'normalization': {},
                'truthy_values': {}
            }
        }, context=context)

        self.assertFalse(serializer.is_valid())
        self.assertIn('scrape_interval', serializer.errors)

    def test_haunt_serializer_validate_alert_mode(self):
        """Test that alert mode validation works"""
        context = self.get_serializer_context()

        serializer = HauntSerializer(data={
            'name': 'Invalid Alert Mode',
            'url': 'https://example.com/invalid',
            'alert_mode': 'invalid_mode',
            'config': {
                'selectors': {},
                'normalization': {},
                'truthy_values': {}
            }
        }, context=context)

        self.assertFalse(serializer.is_valid())
        self.assertIn('alert_mode', serializer.errors)

    def test_haunt_serializer_create_sets_owner(self):
        """Test that create method sets owner from request"""
        context = self.get_serializer_context()

        serializer = HauntSerializer(data={
            'name': 'New Haunt',
            'url': 'https://example.com/new',
            'config': {
                'selectors': {},
                'normalization': {},
                'truthy_values': {}
            }
        }, context=context)

        self.assertTrue(serializer.is_valid())
        haunt = serializer.save()

        self.assertEqual(haunt.owner, self.user)

    def test_haunt_serializer_empty_config_allowed(self):
        """Test that empty config dict is allowed"""
        context = self.get_serializer_context()

        serializer = HauntSerializer(data={
            'name': 'Empty Config',
            'url': 'https://example.com/empty',
            'config': {}
        }, context=context)

        self.assertTrue(serializer.is_valid())


class HauntListSerializerTestCase(TestCase):
    """Test case for HauntListSerializer"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.folder = Folder.objects.create(
            user=self.user,
            name='Test Folder'
        )
        self.haunt = Haunt.objects.create(
            owner=self.user,
            name='Test Haunt',
            url='https://example.com',
            folder=self.folder
        )

    def get_serializer_context(self):
        """Create serializer context with request"""
        request = self.factory.get('/')
        request.user = self.user
        return {'request': request}

    def test_haunt_list_serializer_includes_essential_fields(self):
        """Test that HauntListSerializer includes essential fields only"""
        context = self.get_serializer_context()
        serializer = HauntListSerializer(self.haunt, context=context)
        data = serializer.data

        expected_fields = [
            'id', 'name', 'url', 'is_public', 'is_active', 'folder',
            'folder_name', 'unread_count', 'scrape_interval',
            'scrape_interval_display', 'last_scraped_at', 'is_healthy',
            'is_subscribed', 'owner_email', 'created_at'
        ]

        for field in expected_fields:
            self.assertIn(field, data, f"Field '{field}' missing from list serializer")

    def test_haunt_list_serializer_excludes_heavy_fields(self):
        """Test that HauntListSerializer excludes heavy fields"""
        context = self.get_serializer_context()
        serializer = HauntListSerializer(self.haunt, context=context)
        data = serializer.data

        # These fields should not be in list serializer
        excluded_fields = [
            'config', 'current_state', 'last_alert_state', 'description',
            'last_error', 'public_url', 'rss_url'
        ]

        for field in excluded_fields:
            self.assertNotIn(field, data, f"Field '{field}' should not be in list serializer")

    def test_haunt_list_serializer_folder_name(self):
        """Test that folder_name is correctly populated in list serializer"""
        context = self.get_serializer_context()
        serializer = HauntListSerializer(self.haunt, context=context)
        self.assertEqual(serializer.data['folder_name'], 'Test Folder')

    def test_haunt_list_serializer_multiple_haunts(self):
        """Test serializing multiple haunts"""
        haunt2 = Haunt.objects.create(
            owner=self.user,
            name='Second Haunt',
            url='https://example.com/2'
        )

        context = self.get_serializer_context()
        haunts = [self.haunt, haunt2]
        serializer = HauntListSerializer(haunts, many=True, context=context)

        self.assertEqual(len(serializer.data), 2)
        self.assertEqual(serializer.data[0]['name'], 'Test Haunt')
        self.assertEqual(serializer.data[1]['name'], 'Second Haunt')

    def test_haunt_list_serializer_performance_fields(self):
        """Test that performance-related fields are included"""
        context = self.get_serializer_context()
        serializer = HauntListSerializer(self.haunt, context=context)
        data = serializer.data

        # These fields are important for UI performance
        self.assertIn('is_healthy', data)
        self.assertIn('scrape_interval_display', data)
        self.assertIn('unread_count', data)


class HauntListSerializerSubscriptionTestCase(TestCase):
    """Test case for subscription-related fields in HauntListSerializer"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()

        # Create owner user
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='testpass123'
        )

        # Create subscriber user
        self.subscriber = User.objects.create_user(
            username='subscriber',
            email='subscriber@example.com',
            password='testpass123'
        )

        # Create another user (not subscribed)
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )

        # Create a public haunt
        self.public_haunt = Haunt.objects.create(
            owner=self.owner,
            name='Public Haunt',
            url='https://example.com/public',
            description='A public haunt',
            is_public=True
        )

        # Create subscription
        self.subscription = Subscription.objects.create(
            user=self.subscriber,
            haunt=self.public_haunt
        )

    def get_serializer_context(self, user):
        """Create serializer context with request for given user"""
        request = self.factory.get('/')
        request.user = user
        return {'request': request}

    def test_list_serializer_is_subscribed_for_subscriber(self):
        """Test that is_subscribed returns True for subscribed user in list view"""
        context = self.get_serializer_context(self.subscriber)
        serializer = HauntListSerializer(self.public_haunt, context=context)

        self.assertTrue(serializer.data['is_subscribed'])

    def test_list_serializer_is_subscribed_for_owner(self):
        """Test that is_subscribed returns False for owner in list view"""
        context = self.get_serializer_context(self.owner)
        serializer = HauntListSerializer(self.public_haunt, context=context)

        self.assertFalse(serializer.data['is_subscribed'])

    def test_list_serializer_is_subscribed_for_non_subscriber(self):
        """Test that is_subscribed returns False for non-subscribed user in list view"""
        context = self.get_serializer_context(self.other_user)
        serializer = HauntListSerializer(self.public_haunt, context=context)

        self.assertFalse(serializer.data['is_subscribed'])

    def test_list_serializer_is_subscribed_unauthenticated(self):
        """Test that is_subscribed returns False for unauthenticated user in list view"""
        request = self.factory.get('/')
        request.user = None
        context = {'request': request}

        serializer = HauntListSerializer(self.public_haunt, context=context)

        self.assertFalse(serializer.data['is_subscribed'])

    def test_list_serializer_is_subscribed_no_request(self):
        """Test that is_subscribed handles missing request context in list view"""
        serializer = HauntListSerializer(self.public_haunt, context={})

        self.assertFalse(serializer.data['is_subscribed'])

    def test_list_serializer_owner_email_present(self):
        """Test that owner_email is included in list serializer"""
        context = self.get_serializer_context(self.subscriber)
        serializer = HauntListSerializer(self.public_haunt, context=context)

        self.assertIn('owner_email', serializer.data)
        self.assertEqual(serializer.data['owner_email'], 'owner@example.com')

    def test_list_serializer_owner_email_for_own_haunt(self):
        """Test that owner_email is present even for own haunts in list view"""
        context = self.get_serializer_context(self.owner)
        serializer = HauntListSerializer(self.public_haunt, context=context)

        self.assertEqual(serializer.data['owner_email'], 'owner@example.com')

    def test_list_serializer_owner_email_none_when_no_owner(self):
        """Test that owner_email handles haunts with no owner in list view"""
        haunt_no_owner = Haunt(
            name='No Owner Haunt',
            url='https://example.com/noowner',
            owner=None
        )

        context = self.get_serializer_context(self.subscriber)
        serializer = HauntListSerializer(haunt_no_owner, context=context)

        self.assertIsNone(serializer.data['owner_email'])

    def test_list_serializer_multiple_haunts_subscription_status(self):
        """Test subscription status for multiple haunts in list view"""
        # Create another public haunt (not subscribed)
        other_haunt = Haunt.objects.create(
            owner=self.owner,
            name='Another Public Haunt',
            url='https://example.com/other',
            is_public=True
        )

        context = self.get_serializer_context(self.subscriber)
        haunts = [self.public_haunt, other_haunt]
        serializer = HauntListSerializer(haunts, many=True, context=context)

        # First haunt should be subscribed
        self.assertTrue(serializer.data[0]['is_subscribed'])
        # Second haunt should not be subscribed
        self.assertFalse(serializer.data[1]['is_subscribed'])

    def test_list_serializer_subscription_after_unsubscribe(self):
        """Test that is_subscribed updates after unsubscribing in list view"""
        context = self.get_serializer_context(self.subscriber)

        # Initially subscribed
        serializer = HauntListSerializer(self.public_haunt, context=context)
        self.assertTrue(serializer.data['is_subscribed'])

        # Unsubscribe
        self.subscription.delete()

        # Should now return False
        serializer = HauntListSerializer(self.public_haunt, context=context)
        self.assertFalse(serializer.data['is_subscribed'])

    def test_list_serializer_subscription_after_subscribe(self):
        """Test that is_subscribed updates after subscribing in list view"""
        context = self.get_serializer_context(self.other_user)

        # Initially not subscribed
        serializer = HauntListSerializer(self.public_haunt, context=context)
        self.assertFalse(serializer.data['is_subscribed'])

        # Subscribe
        Subscription.objects.create(
            user=self.other_user,
            haunt=self.public_haunt
        )

        # Should now return True
        serializer = HauntListSerializer(self.public_haunt, context=context)
        self.assertTrue(serializer.data['is_subscribed'])

    def test_list_serializer_mixed_owned_and_subscribed_haunts(self):
        """Test list serializer with mix of owned and subscribed haunts"""
        # Create haunt owned by subscriber
        owned_haunt = Haunt.objects.create(
            owner=self.subscriber,
            name='Owned Haunt',
            url='https://example.com/owned',
            is_public=True
        )

        context = self.get_serializer_context(self.subscriber)
        haunts = [self.public_haunt, owned_haunt]
        serializer = HauntListSerializer(haunts, many=True, context=context)

        # Subscribed haunt should show is_subscribed=True
        self.assertTrue(serializer.data[0]['is_subscribed'])
        self.assertEqual(serializer.data[0]['owner_email'], 'owner@example.com')

        # Owned haunt should show is_subscribed=False
        self.assertFalse(serializer.data[1]['is_subscribed'])
        self.assertEqual(serializer.data[1]['owner_email'], 'subscriber@example.com')

    def test_list_serializer_subscription_query_efficiency(self):
        """Test that subscription check doesn't cause N+1 queries"""
        # Create multiple haunts
        haunts = []
        for i in range(5):
            haunt = Haunt.objects.create(
                owner=self.owner,
                name=f'Haunt {i}',
                url=f'https://example.com/{i}',
                is_public=True
            )
            haunts.append(haunt)

        # Subscribe to some of them
        for haunt in haunts[:3]:
            Subscription.objects.create(
                user=self.subscriber,
                haunt=haunt
            )

        context = self.get_serializer_context(self.subscriber)

        # Serialize all haunts
        serializer = HauntListSerializer(haunts, many=True, context=context)
        data = serializer.data

        # Verify subscription status
        for i in range(5):
            if i < 3:
                self.assertTrue(data[i]['is_subscribed'], f"Haunt {i} should be subscribed")
            else:
                self.assertFalse(data[i]['is_subscribed'], f"Haunt {i} should not be subscribed")

    def test_list_serializer_private_haunt_subscription_fields(self):
        """Test subscription fields work with private haunts in list view"""
        private_haunt = Haunt.objects.create(
            owner=self.owner,
            name='Private Haunt',
            url='https://example.com/private',
            is_public=False
        )

        context = self.get_serializer_context(self.owner)
        serializer = HauntListSerializer(private_haunt, context=context)

        # Owner should not be subscribed to their own haunt
        self.assertFalse(serializer.data['is_subscribed'])
        # Owner email should still be present
        self.assertEqual(serializer.data['owner_email'], 'owner@example.com')

    def test_list_serializer_fields_consistency_with_detail_serializer(self):
        """Test that subscription fields are consistent between list and detail serializers"""
        context = self.get_serializer_context(self.subscriber)

        list_serializer = HauntListSerializer(self.public_haunt, context=context)
        detail_serializer = HauntSerializer(self.public_haunt, context=context)

        # Both should have the same subscription status
        self.assertEqual(
            list_serializer.data['is_subscribed'],
            detail_serializer.data['is_subscribed']
        )

        # Both should have the same owner email
        self.assertEqual(
            list_serializer.data['owner_email'],
            detail_serializer.data['owner_email']
        )

    def test_list_serializer_subscription_with_deleted_user(self):
        """Test that subscription fields handle deleted users gracefully"""
        # This is an edge case - normally cascading deletes would handle this
        # but we test the serializer's robustness
        context = self.get_serializer_context(self.subscriber)
        serializer = HauntListSerializer(self.public_haunt, context=context)

        # Should not raise an error
        self.assertIsNotNone(serializer.data)
        self.assertIn('is_subscribed', serializer.data)
        self.assertIn('owner_email', serializer.data)


class HauntSerializerSubscriptionTestCase(TestCase):
    """Test case for subscription-related serializer methods"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()

        # Create owner user
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='testpass123'
        )

        # Create subscriber user
        self.subscriber = User.objects.create_user(
            username='subscriber',
            email='subscriber@example.com',
            password='testpass123'
        )

        # Create another user (not subscribed)
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )

        # Create a public haunt
        self.public_haunt = Haunt.objects.create(
            owner=self.owner,
            name='Public Haunt',
            url='https://example.com/public',
            description='A public haunt',
            is_public=True,
            config={
                'selectors': {},
                'normalization': {},
                'truthy_values': {}
            }
        )

        # Create a private haunt
        self.private_haunt = Haunt.objects.create(
            owner=self.owner,
            name='Private Haunt',
            url='https://example.com/private',
            description='A private haunt',
            is_public=False,
            config={
                'selectors': {},
                'normalization': {},
                'truthy_values': {}
            }
        )

        # Create subscription
        self.subscription = Subscription.objects.create(
            user=self.subscriber,
            haunt=self.public_haunt
        )

    def get_serializer_context(self, user):
        """Create serializer context with request for given user"""
        request = self.factory.get('/')
        request.user = user
        return {'request': request}

    def test_get_is_subscribed_returns_false_for_unauthenticated(self):
        """Test that is_subscribed returns False for unauthenticated users"""
        request = self.factory.get('/')
        request.user = None
        context = {'request': request}

        serializer = HauntSerializer(self.public_haunt, context=context)
        self.assertFalse(serializer.data['is_subscribed'])

    def test_get_is_subscribed_returns_false_for_owner(self):
        """Test that is_subscribed returns False when user owns the haunt"""
        context = self.get_serializer_context(self.owner)
        serializer = HauntSerializer(self.public_haunt, context=context)

        self.assertFalse(serializer.data['is_subscribed'])

    def test_get_is_subscribed_returns_true_for_subscriber(self):
        """Test that is_subscribed returns True when user is subscribed"""
        context = self.get_serializer_context(self.subscriber)
        serializer = HauntSerializer(self.public_haunt, context=context)

        self.assertTrue(serializer.data['is_subscribed'])

    def test_get_is_subscribed_returns_false_for_non_subscriber(self):
        """Test that is_subscribed returns False when user is not subscribed"""
        context = self.get_serializer_context(self.other_user)
        serializer = HauntSerializer(self.public_haunt, context=context)

        self.assertFalse(serializer.data['is_subscribed'])

    def test_get_is_subscribed_with_no_request_context(self):
        """Test that is_subscribed handles missing request context"""
        serializer = HauntSerializer(self.public_haunt, context={})
        self.assertFalse(serializer.data['is_subscribed'])

    def test_get_is_subscribed_after_unsubscribe(self):
        """Test that is_subscribed returns False after unsubscribing"""
        context = self.get_serializer_context(self.subscriber)

        # Initially subscribed
        serializer = HauntSerializer(self.public_haunt, context=context)
        self.assertTrue(serializer.data['is_subscribed'])

        # Unsubscribe
        self.subscription.delete()

        # Should now return False
        serializer = HauntSerializer(self.public_haunt, context=context)
        self.assertFalse(serializer.data['is_subscribed'])

    def test_get_is_subscribed_multiple_haunts(self):
        """Test is_subscribed with multiple haunts"""
        # Create another public haunt (not subscribed)
        other_haunt = Haunt.objects.create(
            owner=self.owner,
            name='Another Public Haunt',
            url='https://example.com/other',
            is_public=True,
            config={
                'selectors': {},
                'normalization': {},
                'truthy_values': {}
            }
        )

        context = self.get_serializer_context(self.subscriber)

        # Check subscribed haunt
        serializer1 = HauntSerializer(self.public_haunt, context=context)
        self.assertTrue(serializer1.data['is_subscribed'])

        # Check non-subscribed haunt
        serializer2 = HauntSerializer(other_haunt, context=context)
        self.assertFalse(serializer2.data['is_subscribed'])

    def test_get_owner_email_returns_email(self):
        """Test that owner_email returns the owner's email"""
        context = self.get_serializer_context(self.subscriber)
        serializer = HauntSerializer(self.public_haunt, context=context)

        self.assertEqual(serializer.data['owner_email'], 'owner@example.com')

    def test_get_owner_email_for_own_haunt(self):
        """Test that owner_email is returned even for own haunts"""
        context = self.get_serializer_context(self.owner)
        serializer = HauntSerializer(self.public_haunt, context=context)

        self.assertEqual(serializer.data['owner_email'], 'owner@example.com')

    def test_get_owner_email_with_no_owner(self):
        """Test that owner_email handles haunts with no owner gracefully"""
        # Create haunt without owner (edge case)
        haunt_no_owner = Haunt(
            name='No Owner Haunt',
            url='https://example.com/noowner',
            owner=None
        )

        context = self.get_serializer_context(self.subscriber)
        serializer = HauntSerializer(haunt_no_owner, context=context)

        self.assertIsNone(serializer.data['owner_email'])

    def test_owner_email_field_included_in_serializer(self):
        """Test that owner_email field is included in serializer output"""
        context = self.get_serializer_context(self.subscriber)
        serializer = HauntSerializer(self.public_haunt, context=context)

        self.assertIn('owner_email', serializer.data)

    def test_is_subscribed_field_included_in_serializer(self):
        """Test that is_subscribed field is included in serializer output"""
        context = self.get_serializer_context(self.subscriber)
        serializer = HauntSerializer(self.public_haunt, context=context)

        self.assertIn('is_subscribed', serializer.data)

    def test_subscription_fields_with_private_haunt(self):
        """Test subscription fields work correctly with private haunts"""
        context = self.get_serializer_context(self.owner)
        serializer = HauntSerializer(self.private_haunt, context=context)

        # Owner should not be subscribed to their own haunt
        self.assertFalse(serializer.data['is_subscribed'])
        # Owner email should still be present
        self.assertEqual(serializer.data['owner_email'], 'owner@example.com')

    def test_validate_folder_with_valid_folder(self):
        """Test that validate_folder accepts folder belonging to same user"""
        folder = Folder.objects.create(
            user=self.owner,
            name='Owner Folder'
        )

        context = self.get_serializer_context(self.owner)
        serializer = HauntSerializer(data={
            'name': 'Valid Folder Haunt',
            'url': 'https://example.com/valid',
            'folder': folder.id,
            'config': {
                'selectors': {},
                'normalization': {},
                'truthy_values': {}
            }
        }, context=context)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['folder'], folder)

    def test_validate_folder_with_different_user_folder(self):
        """Test that validate_folder rejects folder belonging to different user"""
        other_folder = Folder.objects.create(
            user=self.other_user,
            name='Other User Folder'
        )

        context = self.get_serializer_context(self.owner)
        serializer = HauntSerializer(data={
            'name': 'Invalid Folder Haunt',
            'url': 'https://example.com/invalid',
            'folder': other_folder.id,
            'config': {
                'selectors': {},
                'normalization': {},
                'truthy_values': {}
            }
        }, context=context)

        self.assertFalse(serializer.is_valid())
        self.assertIn('folder', serializer.errors)
        self.assertIn('same user', str(serializer.errors['folder'][0]).lower())

    def test_validate_folder_with_none(self):
        """Test that validate_folder accepts None (no folder)"""
        context = self.get_serializer_context(self.owner)
        serializer = HauntSerializer(data={
            'name': 'No Folder Haunt',
            'url': 'https://example.com/nofolder',
            'folder': None,
            'config': {
                'selectors': {},
                'normalization': {},
                'truthy_values': {}
            }
        }, context=context)

        self.assertTrue(serializer.is_valid())
        self.assertIsNone(serializer.validated_data.get('folder'))

    def test_validate_folder_without_request_context(self):
        """Test that validate_folder handles missing request context"""
        folder = Folder.objects.create(
            user=self.owner,
            name='Test Folder'
        )

        # No request in context
        serializer = HauntSerializer(data={
            'name': 'No Context Haunt',
            'url': 'https://example.com/nocontext',
            'folder': folder.id,
            'config': {
                'selectors': {},
                'normalization': {},
                'truthy_values': {}
            }
        }, context={})

        # Should pass validation since there's no request to check against
        self.assertTrue(serializer.is_valid())

    def test_subscription_status_consistency(self):
        """Test that subscription status is consistent across multiple serializations"""
        context = self.get_serializer_context(self.subscriber)

        # Serialize multiple times
        for _ in range(3):
            serializer = HauntSerializer(self.public_haunt, context=context)
            self.assertTrue(serializer.data['is_subscribed'])

    def test_owner_cannot_be_subscribed_to_own_haunt(self):
        """Test that owner is never considered subscribed to their own haunt"""
        # Even if we somehow create a subscription (which should be prevented)
        # the serializer should still return False for the owner
        context = self.get_serializer_context(self.owner)
        serializer = HauntSerializer(self.public_haunt, context=context)

        self.assertFalse(serializer.data['is_subscribed'])
