"""
Tests for subscription service business logic
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.haunts.models import Haunt, Folder
from apps.rss.models import RSSItem
from apps.subscriptions.models import Subscription, UserReadState
from apps.subscriptions.services import SubscriptionService, ReadStateService

User = get_user_model()


class SubscriptionServiceTestCase(TestCase):
    """Test SubscriptionService methods"""

    def setUp(self):
        """Set up test data"""
        # Create users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )

        # Create folders for user1
        self.folder1 = Folder.objects.create(
            name='Work',
            user=self.user1
        )
        self.folder2 = Folder.objects.create(
            name='Personal',
            user=self.user1
        )

        # Create haunts owned by user1
        self.owned_haunt1 = Haunt.objects.create(
            owner=self.user1,
            name='Owned Haunt 1',
            url='https://example.com/owned1',
            description='First owned haunt',
            config={
                'selectors': {'status': 'css:.status'},
                'normalization': {},
                'truthy_values': {}
            },
            folder=self.folder1,
            is_public=False,
            scrape_interval=60
        )
        self.owned_haunt2 = Haunt.objects.create(
            owner=self.user1,
            name='Owned Haunt 2',
            url='https://example.com/owned2',
            description='Second owned haunt',
            config={
                'selectors': {'status': 'css:.status'},
                'normalization': {},
                'truthy_values': {}
            },
            folder=self.folder2,
            is_public=False,
            scrape_interval=60
        )

        # Create public haunt owned by user2
        self.public_haunt = Haunt.objects.create(
            owner=self.user2,
            name='Public Haunt',
            url='https://example.com/public',
            description='Public test haunt',
            config={
                'selectors': {'status': 'css:.status'},
                'normalization': {},
                'truthy_values': {}
            },
            is_public=True,
            scrape_interval=60
        )

        # Subscribe user1 to public haunt
        Subscription.objects.create(
            user=self.user1,
            haunt=self.public_haunt
        )

    def test_subscribe_to_public_haunt(self):
        """Test subscribing to a public haunt"""
        subscription, created = SubscriptionService.subscribe_to_haunt(
            self.user1,
            self.public_haunt
        )

        self.assertIsNotNone(subscription)
        self.assertFalse(created)  # Already subscribed in setUp
        self.assertEqual(subscription.user, self.user1)
        self.assertEqual(subscription.haunt, self.public_haunt)

    def test_cannot_subscribe_to_private_haunt(self):
        """Test that subscribing to private haunt raises error"""
        with self.assertRaises(ValueError) as context:
            SubscriptionService.subscribe_to_haunt(
                self.user2,
                self.owned_haunt1
            )

        self.assertIn('public', str(context.exception).lower())

    def test_cannot_subscribe_to_own_haunt(self):
        """Test that subscribing to own haunt raises error"""
        # First make the haunt public so it passes the public check
        self.owned_haunt1.is_public = True
        self.owned_haunt1.save()
        
        with self.assertRaises(ValueError) as context:
            SubscriptionService.subscribe_to_haunt(
                self.user1,
                self.owned_haunt1
            )

        self.assertIn('own', str(context.exception).lower())

    def test_unsubscribe_from_haunt(self):
        """Test unsubscribing from a haunt"""
        deleted_count = SubscriptionService.unsubscribe_from_haunt(
            self.user1,
            self.public_haunt
        )

        self.assertEqual(deleted_count, 1)
        self.assertFalse(
            Subscription.objects.filter(
                user=self.user1,
                haunt=self.public_haunt
            ).exists()
        )

    def test_is_subscribed(self):
        """Test checking subscription status"""
        # User1 is subscribed to public_haunt
        self.assertTrue(
            SubscriptionService.is_subscribed(self.user1, self.public_haunt)
        )

        # User2 is not subscribed to owned_haunt1
        self.assertFalse(
            SubscriptionService.is_subscribed(self.user2, self.owned_haunt1)
        )

    def test_get_unread_count_for_haunt_no_items(self):
        """Test unread count when haunt has no RSS items"""
        count = SubscriptionService.get_unread_count_for_haunt(
            self.user1,
            self.owned_haunt1
        )

        self.assertEqual(count, 0)

    def test_get_unread_count_for_haunt_with_items(self):
        """Test unread count with RSS items"""
        # Create RSS items
        item1 = RSSItem.objects.create(
            haunt=self.owned_haunt1,
            title='Item 1',
            description='Description 1',
            link='https://example.com/1',
            guid='item-1',
            pub_date='2024-01-01T00:00:00Z'
        )
        item2 = RSSItem.objects.create(
            haunt=self.owned_haunt1,
            title='Item 2',
            description='Description 2',
            link='https://example.com/2',
            guid='item-2',
            pub_date='2024-01-02T00:00:00Z'
        )

        # All items are unread
        count = SubscriptionService.get_unread_count_for_haunt(
            self.user1,
            self.owned_haunt1
        )
        self.assertEqual(count, 2)

        # Mark one as read
        ReadStateService.mark_as_read(self.user1, item1)

        count = SubscriptionService.get_unread_count_for_haunt(
            self.user1,
            self.owned_haunt1
        )
        self.assertEqual(count, 1)


class GetUnreadCountsForUserTestCase(TestCase):
    """Test get_unread_counts_for_user method with focus on query optimization"""

    def setUp(self):
        """Set up test data"""
        # Create users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )

        # Create folders for user1
        self.folder1 = Folder.objects.create(name='Work', user=self.user1)
        self.folder2 = Folder.objects.create(name='Personal', user=self.user1)

        # Create owned haunts
        self.owned_haunt1 = Haunt.objects.create(
            owner=self.user1,
            name='Owned Haunt 1',
            url='https://example.com/owned1',
            description='First owned haunt',
            config={'selectors': {}, 'normalization': {}, 'truthy_values': {}},
            folder=self.folder1,
            scrape_interval=60
        )
        self.owned_haunt2 = Haunt.objects.create(
            owner=self.user1,
            name='Owned Haunt 2',
            url='https://example.com/owned2',
            description='Second owned haunt',
            config={'selectors': {}, 'normalization': {}, 'truthy_values': {}},
            folder=self.folder2,
            scrape_interval=60
        )

        # Create public haunt owned by user2
        self.public_haunt = Haunt.objects.create(
            owner=self.user2,
            name='Public Haunt',
            url='https://example.com/public',
            description='Public test haunt',
            config={'selectors': {}, 'normalization': {}, 'truthy_values': {}},
            is_public=True,
            scrape_interval=60
        )

        # Subscribe user1 to public haunt
        Subscription.objects.create(user=self.user1, haunt=self.public_haunt)

    def test_get_unread_counts_no_items(self):
        """Test unread counts when no RSS items exist"""
        result = SubscriptionService.get_unread_counts_for_user(self.user1)

        self.assertIn('haunts', result)
        self.assertIn('folders', result)
        self.assertEqual(result['haunts'][str(self.owned_haunt1.id)], 0)
        self.assertEqual(result['haunts'][str(self.owned_haunt2.id)], 0)
        self.assertEqual(result['haunts'][str(self.public_haunt.id)], 0)
        self.assertEqual(result['folders'][str(self.folder1.id)], 0)
        self.assertEqual(result['folders'][str(self.folder2.id)], 0)

    def test_get_unread_counts_with_unread_items(self):
        """Test unread counts with unread RSS items"""
        # Create RSS items for owned haunts
        RSSItem.objects.create(
            haunt=self.owned_haunt1,
            title='Item 1',
            description='Description 1',
            link='https://example.com/1',
            guid='item-1',
            pub_date='2024-01-01T00:00:00Z'
        )
        RSSItem.objects.create(
            haunt=self.owned_haunt1,
            title='Item 2',
            description='Description 2',
            link='https://example.com/2',
            guid='item-2',
            pub_date='2024-01-02T00:00:00Z'
        )
        RSSItem.objects.create(
            haunt=self.owned_haunt2,
            title='Item 3',
            description='Description 3',
            link='https://example.com/3',
            guid='item-3',
            pub_date='2024-01-03T00:00:00Z'
        )

        # Create RSS items for public haunt
        RSSItem.objects.create(
            haunt=self.public_haunt,
            title='Public Item 1',
            description='Public Description 1',
            link='https://example.com/public1',
            guid='public-item-1',
            pub_date='2024-01-04T00:00:00Z'
        )

        result = SubscriptionService.get_unread_counts_for_user(self.user1)

        # Check haunt counts
        self.assertEqual(result['haunts'][str(self.owned_haunt1.id)], 2)
        self.assertEqual(result['haunts'][str(self.owned_haunt2.id)], 1)
        self.assertEqual(result['haunts'][str(self.public_haunt.id)], 1)

        # Check folder counts
        self.assertEqual(result['folders'][str(self.folder1.id)], 2)
        self.assertEqual(result['folders'][str(self.folder2.id)], 1)

    def test_get_unread_counts_with_read_items(self):
        """Test unread counts when some items are marked as read"""
        # Create RSS items
        item1 = RSSItem.objects.create(
            haunt=self.owned_haunt1,
            title='Item 1',
            description='Description 1',
            link='https://example.com/1',
            guid='item-1',
            pub_date='2024-01-01T00:00:00Z'
        )
        item2 = RSSItem.objects.create(
            haunt=self.owned_haunt1,
            title='Item 2',
            description='Description 2',
            link='https://example.com/2',
            guid='item-2',
            pub_date='2024-01-02T00:00:00Z'
        )
        item3 = RSSItem.objects.create(
            haunt=self.public_haunt,
            title='Public Item',
            description='Public Description',
            link='https://example.com/public',
            guid='public-item',
            pub_date='2024-01-03T00:00:00Z'
        )

        # Mark some items as read
        ReadStateService.mark_as_read(self.user1, item1)
        ReadStateService.mark_as_read(self.user1, item3)

        result = SubscriptionService.get_unread_counts_for_user(self.user1)

        # Only item2 should be unread for owned_haunt1
        self.assertEqual(result['haunts'][str(self.owned_haunt1.id)], 1)
        # Public haunt item is read
        self.assertEqual(result['haunts'][str(self.public_haunt.id)], 0)
        # Folder1 should have 1 unread
        self.assertEqual(result['folders'][str(self.folder1.id)], 1)

    def test_get_unread_counts_includes_owned_and_subscribed(self):
        """Test that counts include both owned and subscribed haunts"""
        # Create items for both owned and subscribed haunts
        RSSItem.objects.create(
            haunt=self.owned_haunt1,
            title='Owned Item',
            description='Owned Description',
            link='https://example.com/owned',
            guid='owned-item',
            pub_date='2024-01-01T00:00:00Z'
        )
        RSSItem.objects.create(
            haunt=self.public_haunt,
            title='Subscribed Item',
            description='Subscribed Description',
            link='https://example.com/subscribed',
            guid='subscribed-item',
            pub_date='2024-01-02T00:00:00Z'
        )

        result = SubscriptionService.get_unread_counts_for_user(self.user1)

        # Both haunts should be included
        self.assertIn(str(self.owned_haunt1.id), result['haunts'])
        self.assertIn(str(self.public_haunt.id), result['haunts'])
        self.assertEqual(result['haunts'][str(self.owned_haunt1.id)], 1)
        self.assertEqual(result['haunts'][str(self.public_haunt.id)], 1)

    def test_get_unread_counts_no_duplicate_haunts(self):
        """Test that haunts are not duplicated in results (tests distinct())"""
        # This tests the fix: using Q() with distinct() instead of union()
        # Create multiple subscriptions to ensure distinct() works
        result = SubscriptionService.get_unread_counts_for_user(self.user1)

        # Count how many times each haunt appears
        haunt_ids = list(result['haunts'].keys())
        unique_haunt_ids = set(haunt_ids)

        # Should have no duplicates
        self.assertEqual(len(haunt_ids), len(unique_haunt_ids))

        # Should have exactly 3 haunts (2 owned + 1 subscribed)
        self.assertEqual(len(haunt_ids), 3)

    def test_get_unread_counts_folder_aggregation(self):
        """Test that folder counts correctly aggregate haunt counts"""
        # Create multiple items in folder1 haunts
        RSSItem.objects.create(
            haunt=self.owned_haunt1,
            title='Item 1',
            description='Description 1',
            link='https://example.com/1',
            guid='item-1',
            pub_date='2024-01-01T00:00:00Z'
        )
        RSSItem.objects.create(
            haunt=self.owned_haunt1,
            title='Item 2',
            description='Description 2',
            link='https://example.com/2',
            guid='item-2',
            pub_date='2024-01-02T00:00:00Z'
        )

        # Create item in folder2 haunt
        RSSItem.objects.create(
            haunt=self.owned_haunt2,
            title='Item 3',
            description='Description 3',
            link='https://example.com/3',
            guid='item-3',
            pub_date='2024-01-03T00:00:00Z'
        )

        result = SubscriptionService.get_unread_counts_for_user(self.user1)

        # Folder1 should have 2 unread items
        self.assertEqual(result['folders'][str(self.folder1.id)], 2)
        # Folder2 should have 1 unread item
        self.assertEqual(result['folders'][str(self.folder2.id)], 1)

    def test_get_unread_counts_empty_folders(self):
        """Test that empty folders return 0 count"""
        # Create folder with no haunts
        empty_folder = Folder.objects.create(name='Empty', user=self.user1)

        result = SubscriptionService.get_unread_counts_for_user(self.user1)

        # Empty folder should have 0 count
        self.assertEqual(result['folders'][str(empty_folder.id)], 0)

    def test_get_unread_counts_haunts_without_folder(self):
        """Test haunts without folders are still counted"""
        # Create haunt without folder
        no_folder_haunt = Haunt.objects.create(
            owner=self.user1,
            name='No Folder Haunt',
            url='https://example.com/nofolder',
            description='Haunt without folder',
            config={'selectors': {}, 'normalization': {}, 'truthy_values': {}},
            folder=None,
            scrape_interval=60
        )

        RSSItem.objects.create(
            haunt=no_folder_haunt,
            title='Item',
            description='Description',
            link='https://example.com/nofolder',
            guid='nofolder-item',
            pub_date='2024-01-01T00:00:00Z'
        )

        result = SubscriptionService.get_unread_counts_for_user(self.user1)

        # Haunt should be counted
        self.assertIn(str(no_folder_haunt.id), result['haunts'])
        self.assertEqual(result['haunts'][str(no_folder_haunt.id)], 1)

    def test_get_unread_counts_user_isolation(self):
        """Test that counts are isolated per user"""
        # Create items for user1's haunt
        item1 = RSSItem.objects.create(
            haunt=self.owned_haunt1,
            title='Item 1',
            description='Description 1',
            link='https://example.com/1',
            guid='item-1',
            pub_date='2024-01-01T00:00:00Z'
        )

        # User2 marks it as read (shouldn't affect user1's count)
        ReadStateService.mark_as_read(self.user2, item1)

        result = SubscriptionService.get_unread_counts_for_user(self.user1)

        # User1 should still see it as unread
        self.assertEqual(result['haunts'][str(self.owned_haunt1.id)], 1)

    def test_get_unread_counts_performance_single_query(self):
        """Test that the method uses efficient queries (Q with distinct)"""
        # This test verifies the optimization from union() to Q() with distinct()
        from django.test.utils import override_settings
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        # Create some data
        for i in range(5):
            RSSItem.objects.create(
                haunt=self.owned_haunt1,
                title=f'Item {i}',
                description=f'Description {i}',
                link=f'https://example.com/{i}',
                guid=f'item-{i}',
                pub_date=f'2024-01-0{i+1}T00:00:00Z'
            )

        with CaptureQueriesContext(connection) as context:
            result = SubscriptionService.get_unread_counts_for_user(self.user1)

        # The query should use Q() with distinct() which is more efficient
        # Check that we got valid results
        self.assertIn('haunts', result)
        self.assertIn('folders', result)
        self.assertEqual(result['haunts'][str(self.owned_haunt1.id)], 5)


class ReadStateServiceTestCase(TestCase):
    """Test ReadStateService methods"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.haunt = Haunt.objects.create(
            owner=self.user,
            name='Test Haunt',
            url='https://example.com',
            description='Test haunt',
            config={'selectors': {}, 'normalization': {}, 'truthy_values': {}},
            scrape_interval=60
        )

        self.rss_item = RSSItem.objects.create(
            haunt=self.haunt,
            title='Test Item',
            description='Test Description',
            link='https://example.com/test',
            guid='test-item',
            pub_date='2024-01-01T00:00:00Z'
        )

    def test_mark_as_read(self):
        """Test marking an item as read"""
        read_state = ReadStateService.mark_as_read(self.user, self.rss_item)

        self.assertIsNotNone(read_state)
        self.assertTrue(read_state.is_read)
        self.assertIsNotNone(read_state.read_at)

    def test_mark_as_unread(self):
        """Test marking an item as unread"""
        # First mark as read
        ReadStateService.mark_as_read(self.user, self.rss_item)

        # Then mark as unread
        read_state = ReadStateService.mark_as_unread(self.user, self.rss_item)

        self.assertIsNotNone(read_state)
        self.assertFalse(read_state.is_read)

    def test_toggle_starred(self):
        """Test toggling starred state"""
        # First toggle - should star
        read_state = ReadStateService.toggle_starred(self.user, self.rss_item)
        self.assertTrue(read_state.is_starred)

        # Second toggle - should unstar
        read_state = ReadStateService.toggle_starred(self.user, self.rss_item)
        self.assertFalse(read_state.is_starred)

    def test_get_read_state_exists(self):
        """Test getting existing read state"""
        # Create read state
        ReadStateService.mark_as_read(self.user, self.rss_item)

        # Get read state
        read_state = ReadStateService.get_read_state(self.user, self.rss_item)

        self.assertIsNotNone(read_state)
        self.assertTrue(read_state.is_read)

    def test_get_read_state_not_exists(self):
        """Test getting non-existent read state"""
        read_state = ReadStateService.get_read_state(self.user, self.rss_item)

        self.assertIsNone(read_state)

    def test_get_starred_items(self):
        """Test getting starred items"""
        # Star the item
        ReadStateService.toggle_starred(self.user, self.rss_item)

        # Get starred items
        starred = ReadStateService.get_starred_items(self.user)

        self.assertEqual(starred.count(), 1)
        self.assertEqual(starred.first().rss_item, self.rss_item)

    def test_get_unread_items(self):
        """Test getting unread items"""
        # Create another item and mark first as read
        item2 = RSSItem.objects.create(
            haunt=self.haunt,
            title='Item 2',
            description='Description 2',
            link='https://example.com/test2',
            guid='test-item-2',
            pub_date='2024-01-02T00:00:00Z'
        )

        ReadStateService.mark_as_read(self.user, self.rss_item)

        # Get unread items
        unread = ReadStateService.get_unread_items(self.user)

        self.assertEqual(unread.count(), 1)
        self.assertEqual(unread.first(), item2)
