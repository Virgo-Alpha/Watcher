"""
Unit tests for RSS service.
"""
import xml.etree.ElementTree as ET
from datetime import timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.haunts.models import Haunt
from apps.rss.models import RSSItem
from apps.rss.services import RSSService

User = get_user_model()


class RSSServiceTest(TestCase):
    """Test RSS service functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.haunt = Haunt.objects.create(
            owner=self.user,
            name='Test Haunt',
            url='https://example.com',
            description='Test haunt description',
            config={
                'selectors': {'status': 'css:.status'},
                'normalization': {},
                'truthy_values': {}
            },
            scrape_interval=60
        )

        self.service = RSSService()

    def test_create_rss_item(self):
        """Test creating an RSS item from changes."""
        changes = {
            'status': {'old': 'closed', 'new': 'open'}
        }

        rss_item = self.service.create_rss_item(
            haunt=self.haunt,
            changes=changes
        )

        self.assertIsNotNone(rss_item)
        self.assertEqual(rss_item.haunt, self.haunt)
        self.assertEqual(rss_item.link, self.haunt.url)
        self.assertIn('status', rss_item.title)
        self.assertIn('open', rss_item.title)
        self.assertEqual(rss_item.change_data, changes)

    def test_create_rss_item_with_ai_summary(self):
        """Test creating an RSS item with AI summary."""
        changes = {
            'status': {'old': 'closed', 'new': 'open'}
        }
        ai_summary = 'The status changed from closed to open.'

        rss_item = self.service.create_rss_item(
            haunt=self.haunt,
            changes=changes,
            ai_summary=ai_summary
        )

        self.assertEqual(rss_item.ai_summary, ai_summary)
        self.assertEqual(rss_item.description, ai_summary)

    def test_generate_title_single_change(self):
        """Test title generation with single change."""
        changes = {
            'status': {'old': 'closed', 'new': 'open'}
        }

        title = self.service._generate_title(self.haunt, changes)

        self.assertIn('Test Haunt', title)
        self.assertIn('status', title)
        self.assertIn('open', title)

    def test_generate_title_multiple_changes(self):
        """Test title generation with multiple changes."""
        changes = {
            'status': {'old': 'closed', 'new': 'open'},
            'deadline': {'old': '2024-01-01', 'new': '2024-02-01'}
        }

        title = self.service._generate_title(self.haunt, changes)

        self.assertIn('Test Haunt', title)
        self.assertIn('and 1 more', title)

    def test_generate_description_with_ai_summary(self):
        """Test description generation with AI summary."""
        changes = {'status': {'old': 'closed', 'new': 'open'}}
        ai_summary = 'The status changed from closed to open.'

        description = self.service._generate_description(changes, ai_summary)

        self.assertEqual(description, ai_summary)

    def test_generate_description_without_ai_summary(self):
        """Test description generation without AI summary."""
        changes = {
            'status': {'old': 'closed', 'new': 'open'},
            'deadline': {'old': '2024-01-01', 'new': '2024-02-01'}
        }

        description = self.service._generate_description(changes)

        self.assertIn('status: closed → open', description)
        self.assertIn('deadline: 2024-01-01 → 2024-02-01', description)

    def test_get_recent_items(self):
        """Test retrieving recent RSS items."""
        # Create multiple RSS items
        for i in range(5):
            RSSItem.objects.create(
                haunt=self.haunt,
                title=f'Change {i}',
                description=f'Description {i}',
                link=self.haunt.url,
                pub_date=timezone.now() - timedelta(hours=i)
            )

        items = self.service.get_recent_items(self.haunt, limit=3)

        self.assertEqual(len(items), 3)
        # Should be ordered by pub_date descending
        self.assertEqual(items[0].title, 'Change 0')

    def test_generate_rss_feed(self):
        """Test RSS feed XML generation."""
        # Create RSS items
        RSSItem.objects.create(
            haunt=self.haunt,
            title='Status changed',
            description='Status: closed → open',
            link=self.haunt.url,
            pub_date=timezone.now()
        )

        feed_xml = self.service.generate_rss_feed(self.haunt)

        # Verify it's valid XML
        root = ET.fromstring(feed_xml)
        self.assertEqual(root.tag, 'rss')
        self.assertEqual(root.get('version'), '2.0')

        # Verify channel elements
        channel = root.find('channel')
        self.assertIsNotNone(channel)

        title = channel.find('title')
        self.assertEqual(title.text, 'Test Haunt')

        link = channel.find('link')
        self.assertEqual(link.text, 'https://example.com')

        description = channel.find('description')
        self.assertIn('Test haunt description', description.text)

        # Verify item elements
        items = channel.findall('item')
        self.assertEqual(len(items), 1)

        item = items[0]
        item_title = item.find('title')
        self.assertEqual(item_title.text, 'Status changed')

    def test_generate_rss_feed_with_ai_summary(self):
        """Test RSS feed generation with AI summary in description."""
        RSSItem.objects.create(
            haunt=self.haunt,
            title='Status changed',
            description='Status: closed → open',
            link=self.haunt.url,
            pub_date=timezone.now(),
            ai_summary='The application status has changed to open.'
        )

        feed_xml = self.service.generate_rss_feed(self.haunt)

        root = ET.fromstring(feed_xml)
        channel = root.find('channel')
        items = channel.findall('item')
        item = items[0]

        description = item.find('description')
        # Should include AI summary
        self.assertIn('Summary:', description.text)
        self.assertIn('The application status has changed to open.', description.text)

    def test_format_rfc822_date(self):
        """Test RFC 822 date formatting."""
        dt = timezone.make_aware(timezone.datetime(2024, 1, 15, 12, 30, 0))

        formatted = self.service._format_rfc822_date(dt)

        # Should be in RFC 822 format
        self.assertIn('Mon', formatted)
        self.assertIn('15 Jan 2024', formatted)
        self.assertIn('12:30:00', formatted)

    def test_generate_rss_feed_empty_items(self):
        """Test RSS feed generation with no items."""
        feed_xml = self.service.generate_rss_feed(self.haunt)

        root = ET.fromstring(feed_xml)
        channel = root.find('channel')
        items = channel.findall('item')

        # Should have no items but still be valid RSS
        self.assertEqual(len(items), 0)
        self.assertIsNotNone(channel.find('title'))
        self.assertIsNotNone(channel.find('link'))

    def test_generate_rss_feed_respects_limit(self):
        """Test RSS feed generation respects item limit."""
        # Create 10 RSS items
        for i in range(10):
            RSSItem.objects.create(
                haunt=self.haunt,
                title=f'Change {i}',
                description=f'Description {i}',
                link=self.haunt.url,
                pub_date=timezone.now() - timedelta(hours=i)
            )

        feed_xml = self.service.generate_rss_feed(self.haunt, limit=5)

        root = ET.fromstring(feed_xml)
        channel = root.find('channel')
        items = channel.findall('item')

        self.assertEqual(len(items), 5)
