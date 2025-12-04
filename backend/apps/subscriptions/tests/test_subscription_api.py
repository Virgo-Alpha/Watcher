"""
Tests for subscription API endpoints
"""
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
