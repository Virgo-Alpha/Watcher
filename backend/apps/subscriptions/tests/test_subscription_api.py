"""
Tests for subscription API endpoints
"""
from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.haunts.models import Haunt
from apps.subscriptions.models import Subscription

User = get_user_model()


class SubscriptionAPITestCase(TestCase):
    """Test subscription API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

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

        # Create a public haunt owned by user1
        self.public_haunt = Haunt.objects.create(
            owner=self.user1,
            name='Test Public Haunt',
            url='https://example.com',
            description='Test haunt',
            config={
                'selectors': {'status': 'css:.status'},
                'normalization': {},
                'truthy_values': {}
            },
            is_public=True,
            scrape_interval=60
        )

        # Create a private haunt owned by user1
        self.private_haunt = Haunt.objects.create(
            owner=self.user1,
            name='Test Private Haunt',
            url='https://example.com/private',
            description='Private test haunt',
            config={
                'selectors': {'status': 'css:.status'},
                'normalization': {},
                'truthy_values': {}
            },
            is_public=False,
            scrape_interval=60
        )

    def test_subscribe_to_public_haunt(self):
        """Test subscribing to a public haunt"""
        self.client.force_authenticate(user=self.user2)

        response = self.client.post('/api/v1/subscriptions/', {
            'haunt_id': str(self.public_haunt.id),
            'notifications_enabled': True
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['haunt'], self.public_haunt.id)

        # Verify subscription was created
        self.assertTrue(
            Subscription.objects.filter(
                user=self.user2,
                haunt=self.public_haunt
            ).exists()
        )

    def test_cannot_subscribe_to_private_haunt(self):
        """Test that users cannot subscribe to private haunts"""
        self.client.force_authenticate(user=self.user2)

        response = self.client.post('/api/v1/subscriptions/', {
            'haunt_id': str(self.private_haunt.id),
            'notifications_enabled': True
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Verify subscription was not created
        self.assertFalse(
            Subscription.objects.filter(
                user=self.user2,
                haunt=self.private_haunt
            ).exists()
        )

    def test_cannot_subscribe_to_own_haunt(self):
        """Test that users cannot subscribe to their own haunts"""
        self.client.force_authenticate(user=self.user1)

        response = self.client.post('/api/v1/subscriptions/', {
            'haunt_id': str(self.public_haunt.id),
            'notifications_enabled': True
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_subscriptions(self):
        """Test listing user subscriptions"""
        # Create subscription
        Subscription.objects.create(
            user=self.user2,
            haunt=self.public_haunt
        )

        self.client.force_authenticate(user=self.user2)
        response = self.client.get('/api/v1/subscriptions/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['haunt'], self.public_haunt.id)

    def test_unsubscribe(self):
        """Test unsubscribing from a haunt"""
        # Create subscription
        subscription = Subscription.objects.create(
            user=self.user2,
            haunt=self.public_haunt
        )

        self.client.force_authenticate(user=self.user2)
        response = self.client.delete(f'/api/v1/subscriptions/{subscription.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify subscription was deleted
        self.assertFalse(
            Subscription.objects.filter(id=subscription.id).exists()
        )

    def test_check_subscription_status(self):
        """Test checking if user is subscribed to a haunt"""
        self.client.force_authenticate(user=self.user2)

        # Check when not subscribed
        response = self.client.get(
            f'/api/v1/subscriptions/check_subscription/?haunt_id={self.public_haunt.id}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_subscribed'])

        # Create subscription
        Subscription.objects.create(
            user=self.user2,
            haunt=self.public_haunt
        )

        # Check when subscribed
        response = self.client.get(
            f'/api/v1/subscriptions/check_subscription/?haunt_id={self.public_haunt.id}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_subscribed'])

    def test_duplicate_subscription_returns_200(self):
        """Test that subscribing twice to the same haunt returns 200"""
        self.client.force_authenticate(user=self.user2)

        # First subscription
        response1 = self.client.post('/api/v1/subscriptions/', {
            'haunt_id': str(self.public_haunt.id),
            'notifications_enabled': True
        })
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Second subscription attempt
        response2 = self.client.post('/api/v1/subscriptions/', {
            'haunt_id': str(self.public_haunt.id),
            'notifications_enabled': True
        })
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertIn('Already subscribed', response2.data['message'])

        # Verify only one subscription exists
        self.assertEqual(
            Subscription.objects.filter(
                user=self.user2,
                haunt=self.public_haunt
            ).count(),
            1
        )

    def test_subscribe_with_invalid_haunt_id(self):
        """Test subscribing with invalid haunt ID"""
        self.client.force_authenticate(user=self.user2)

        response = self.client.post('/api/v1/subscriptions/', {
            'haunt_id': 'invalid-uuid',
            'notifications_enabled': True
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_subscribe_with_nonexistent_haunt(self):
        """Test subscribing to a haunt that doesn't exist"""
        self.client.force_authenticate(user=self.user2)

        response = self.client.post('/api/v1/subscriptions/', {
            'haunt_id': '00000000-0000-0000-0000-000000000000',
            'notifications_enabled': True
        })

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Haunt not found', response.data['error'])

    def test_subscribe_without_authentication(self):
        """Test that unauthenticated users cannot subscribe"""
        response = self.client.post('/api/v1/subscriptions/', {
            'haunt_id': str(self.public_haunt.id),
            'notifications_enabled': True
        })

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_subscription_notifications(self):
        """Test updating subscription notification settings"""
        # Create subscription
        subscription = Subscription.objects.create(
            user=self.user2,
            haunt=self.public_haunt,
            notifications_enabled=True
        )

        self.client.force_authenticate(user=self.user2)
        response = self.client.patch(
            f'/api/v1/subscriptions/{subscription.id}/',
            {'notifications_enabled': False}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['notifications_enabled'])

        # Verify database was updated
        subscription.refresh_from_db()
        self.assertFalse(subscription.notifications_enabled)

    def test_unsubscribe_by_haunt_id(self):
        """Test unsubscribing using haunt ID"""
        # Create subscription
        Subscription.objects.create(
            user=self.user2,
            haunt=self.public_haunt
        )

        self.client.force_authenticate(user=self.user2)
        response = self.client.post(
            '/api/v1/subscriptions/unsubscribe_by_haunt/',
            {'haunt_id': str(self.public_haunt.id)}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Successfully unsubscribed', response.data['message'])

        # Verify subscription was deleted
        self.assertFalse(
            Subscription.objects.filter(
                user=self.user2,
                haunt=self.public_haunt
            ).exists()
        )

    def test_unsubscribe_by_haunt_when_not_subscribed(self):
        """Test unsubscribing from a haunt when not subscribed"""
        self.client.force_authenticate(user=self.user2)

        response = self.client.post(
            '/api/v1/subscriptions/unsubscribe_by_haunt/',
            {'haunt_id': str(self.public_haunt.id)}
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Not subscribed', response.data['message'])

    def test_filter_subscriptions_by_haunt(self):
        """Test filtering subscriptions by haunt ID"""
        # Create another public haunt
        haunt2 = Haunt.objects.create(
            owner=self.user1,
            name='Second Public Haunt',
            url='https://example.com/second',
            description='Second test haunt',
            config={
                'selectors': {'status': 'css:.status'},
                'normalization': {},
                'truthy_values': {}
            },
            is_public=True,
            scrape_interval=60
        )

        # Create subscriptions
        Subscription.objects.create(user=self.user2, haunt=self.public_haunt)
        Subscription.objects.create(user=self.user2, haunt=haunt2)

        self.client.force_authenticate(user=self.user2)

        # Filter by first haunt
        response = self.client.get(
            f'/api/v1/subscriptions/?haunt={self.public_haunt.id}'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['haunt'], self.public_haunt.id)

    @patch('apps.subscriptions.views.logger')
    def test_logging_on_successful_subscription(self, mock_logger):
        """Test that successful subscription logs correctly"""
        self.client.force_authenticate(user=self.user2)

        response = self.client.post('/api/v1/subscriptions/', {
            'haunt_id': str(self.public_haunt.id),
            'notifications_enabled': True
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify logging calls
        self.assertTrue(mock_logger.info.called)
        # Check that the info log was called with user and content-type
        call_args = [call[0][0] for call in mock_logger.info.call_args_list]
        self.assertTrue(
            any('Subscription create request' in arg for arg in call_args)
        )
        self.assertTrue(
            any('subscribed to haunt' in arg for arg in call_args)
        )

    @patch('apps.subscriptions.views.logger')
    def test_logging_on_validation_failure(self, mock_logger):
        """Test that validation failures log correctly"""
        self.client.force_authenticate(user=self.user2)

        # Try to subscribe with invalid data
        response = self.client.post('/api/v1/subscriptions/', {
            'haunt_id': 'invalid-uuid',
            'notifications_enabled': True
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Verify error logging
        self.assertTrue(mock_logger.error.called)
        error_call = mock_logger.error.call_args[0][0]
        self.assertIn('Subscription validation failed', error_call)

    @patch('apps.subscriptions.views.logger')
    def test_logging_on_unsubscribe(self, mock_logger):
        """Test that unsubscribe logs correctly"""
        # Create subscription
        subscription = Subscription.objects.create(
            user=self.user2,
            haunt=self.public_haunt
        )

        self.client.force_authenticate(user=self.user2)
        response = self.client.delete(f'/api/v1/subscriptions/{subscription.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify logging
        self.assertTrue(mock_logger.info.called)
        call_args = [call[0][0] for call in mock_logger.info.call_args_list]
        self.assertTrue(
            any('unsubscribed from haunt' in arg for arg in call_args)
        )
