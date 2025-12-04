"""
Tests for read state tracking functionality
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.haunts.models import Haunt
from apps.rss.models import RSSItem
from apps.subscriptions.models import UserReadState
from apps.subscriptions.services import ReadStateService

User = get_user_model()


class ReadStateTestCase(TestCase):
    """Test read state tracking"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create haunt
        self.haunt = Haunt.objects.create(
            owner=self.user,
            name='Test Haunt',
            url='https://example.com',
            description='Test haunt',
            config={
                'selectors': {'status': 'css:.status'},
                'normalization': {},
                'truthy_values': {}
            },
            scrape_interval=60
        )

        # Create RSS items with explicit GUIDs to avoid conflicts
        import uuid
        self.rss_item1 = RSSItem.objects.create(
            haunt=self.haunt,
            title='Test Item 1',
            description='Description 1',
            link='https://example.com/1',
            guid=f'test-item-1-{uuid.uuid4()}',
            change_data={'status': {'old': 'closed', 'new': 'open'}}
        )

        self.rss_item2 = RSSItem.objects.create(
            haunt=self.haunt,
            title='Test Item 2',
            description='Description 2',
            link='https://example.com/2',
            guid=f'test-item-2-{uuid.uuid4()}',
            change_data={'status': {'old': 'open', 'new': 'closed'}}
        )

    def test_mark_as_read(self):
        """Test marking an item as read"""
        self.client.force_authenticate(user=self.user)

        response = self.client.post('/api/v1/read-states/mark_read/', {
            'rss_item_id': str(self.rss_item1.id)
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_read'])

        # Verify read state was created
        read_state = UserReadState.objects.get(
            user=self.user,
            rss_item=self.rss_item1
        )
        self.assertTrue(read_state.is_read)
        self.assertIsNotNone(read_state.read_at)

    def test_mark_as_unread(self):
        """Test marking an item as unread"""
        # First mark as read
        ReadStateService.mark_as_read(self.user, self.rss_item1)

        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/v1/read-states/mark_unread/', {
            'rss_item_id': str(self.rss_item1.id)
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_read'])

        # Verify read state was updated
        read_state = UserReadState.objects.get(
            user=self.user,
            rss_item=self.rss_item1
        )
        self.assertFalse(read_state.is_read)
        self.assertIsNone(read_state.read_at)

    def test_toggle_starred(self):
        """Test toggling starred state"""
        self.client.force_authenticate(user=self.user)

        # Star the item
        response = self.client.post('/api/v1/read-states/toggle_starred/', {
            'rss_item_id': str(self.rss_item1.id)
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['read_state']['is_starred'])

        # Unstar the item
        response = self.client.post('/api/v1/read-states/toggle_starred/', {
            'rss_item_id': str(self.rss_item1.id)
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['read_state']['is_starred'])

    def test_bulk_mark_read(self):
        """Test bulk marking items as read"""
        self.client.force_authenticate(user=self.user)

        response = self.client.post('/api/v1/read-states/bulk_mark_read/', {
            'rss_item_ids': [str(self.rss_item1.id), str(self.rss_item2.id)],
            'is_read': True
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['updated_count'], 2)

        # Verify both items are marked as read
        read_states = UserReadState.objects.filter(
            user=self.user,
            rss_item__in=[self.rss_item1, self.rss_item2],
            is_read=True
        )
        self.assertEqual(read_states.count(), 2)

    def test_get_starred_items(self):
        """Test getting starred items"""
        # Star an item
        ReadStateService.toggle_starred(self.user, self.rss_item1)

        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/read-states/starred_items/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(
            response.data['results'][0]['rss_item'],
            self.rss_item1.id
        )

    def test_get_unread_items(self):
        """Test getting unread items"""
        # Mark one item as read
        ReadStateService.mark_as_read(self.user, self.rss_item1)

        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/read-states/unread_items/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return the unread item
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(str(response.data['results'][0]['id']), str(self.rss_item2.id))
