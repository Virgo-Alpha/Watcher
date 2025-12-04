"""
API tests for RSS feed endpoints.
"""
import xml.etree.ElementTree as ET
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.haunts.models import Haunt
from apps.rss.models import RSSItem

User = get_user_model()


class RSSFeedEndpointsTest(TestCase):
    """Test RSS feed API endpoints."""

    def setUp(self):
        """Set up test data."""
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

        # Create haunts
        self.private_haunt = Haunt.objects.create(
            owner=self.user1,
            name='Private Haunt',
            url='https://example.com/private',
            description='Private haunt',
            config={
                'selectors': {'status': 'css:.status'},
                'normalization': {},
                'truthy_values': {}
            },
            scrape_interval=60,
            is_public=False
        )

        self.public_haunt = Haunt.objects.create(
            owner=self.user1,
            name='Public Haunt',
            url='https://example.com/public',
            description='Public haunt',
            config={
                'selectors': {'status': 'css:.status'},
                'normalization': {},
                'truthy_values': {}
            },
            scrape_interval=60,
            is_public=True,
            public_slug='public-haunt'
        )

        # Create RSS items
        RSSItem.objects.create(
            haunt=self.private_haunt,
            title='Private Change',
            description='Private change description',
            link=self.private_haunt.url
        )

        RSSItem.objects.create(
            haunt=self.public_haunt,
            title='Public Change',
            description='Public change description',
            link=self.public_haunt.url
        )

        self.client = APIClient()

    def test_private_rss_feed_authenticated(self):
        """Test accessing private RSS feed with authentication."""
        self.client.force_authenticate(user=self.user1)

        url = reverse('rss:private-feed', kwargs={'haunt_id': self.private_haunt.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/rss+xml; charset=utf-8')

        # Verify XML structure
        root = ET.fromstring(response.content)
        self.assertEqual(root.tag, 'rss')

        channel = root.find('channel')
        self.assertIsNotNone(channel)

        title = channel.find('title')
        self.assertEqual(title.text, 'Private Haunt')

        items = channel.findall('item')
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].find('title').text, 'Private Change')

    def test_private_rss_feed_unauthenticated(self):
        """Test accessing private RSS feed without authentication."""
        url = reverse('rss:private-feed', kwargs={'haunt_id': self.private_haunt.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_private_rss_feed_wrong_owner(self):
        """Test accessing private RSS feed with wrong owner."""
        self.client.force_authenticate(user=self.user2)

        url = reverse('rss:private-feed', kwargs={'haunt_id': self.private_haunt.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_public_rss_feed_unauthenticated(self):
        """Test accessing public RSS feed without authentication."""
        url = reverse('rss:public-feed', kwargs={'public_slug': self.public_haunt.public_slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/rss+xml; charset=utf-8')

        # Verify XML structure
        root = ET.fromstring(response.content)
        self.assertEqual(root.tag, 'rss')

        channel = root.find('channel')
        title = channel.find('title')
        self.assertEqual(title.text, 'Public Haunt')

        items = channel.findall('item')
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].find('title').text, 'Public Change')

    def test_public_rss_feed_authenticated(self):
        """Test accessing public RSS feed with authentication."""
        self.client.force_authenticate(user=self.user2)

        url = reverse('rss:public-feed', kwargs={'public_slug': self.public_haunt.public_slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_public_rss_feed_invalid_slug(self):
        """Test accessing public RSS feed with invalid slug."""
        url = reverse('rss:public-feed', kwargs={'public_slug': 'nonexistent'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_rss_url_private_haunt(self):
        """Test getting RSS URL for private haunt."""
        self.client.force_authenticate(user=self.user1)

        url = reverse('rss:get-url', kwargs={'haunt_id': self.private_haunt.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('rss_url', response.data)
        self.assertIn(f'/rss/private/{self.private_haunt.id}/', response.data['rss_url'])
        self.assertFalse(response.data['is_public'])

    def test_get_rss_url_public_haunt(self):
        """Test getting RSS URL for public haunt."""
        self.client.force_authenticate(user=self.user1)

        url = reverse('rss:get-url', kwargs={'haunt_id': self.public_haunt.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('rss_url', response.data)
        self.assertIn(f'/rss/public/{self.public_haunt.public_slug}/', response.data['rss_url'])
        self.assertTrue(response.data['is_public'])

    def test_get_rss_url_unauthenticated(self):
        """Test getting RSS URL without authentication."""
        url = reverse('rss:get-url', kwargs={'haunt_id': self.private_haunt.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_rss_url_wrong_owner(self):
        """Test getting RSS URL with wrong owner."""
        self.client.force_authenticate(user=self.user2)

        url = reverse('rss:get-url', kwargs={'haunt_id': self.private_haunt.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_rss_feed_content_type(self):
        """Test RSS feed returns correct content type."""
        url = reverse('rss:public-feed', kwargs={'public_slug': self.public_haunt.public_slug})
        response = self.client.get(url)

        self.assertEqual(response['Content-Type'], 'application/rss+xml; charset=utf-8')

    def test_rss_feed_valid_xml(self):
        """Test RSS feed returns valid XML."""
        url = reverse('rss:public-feed', kwargs={'public_slug': self.public_haunt.public_slug})
        response = self.client.get(url)

        # Should not raise exception
        root = ET.fromstring(response.content)
        self.assertEqual(root.tag, 'rss')
        self.assertEqual(root.get('version'), '2.0')
