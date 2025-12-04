"""
Integration tests for Celery scraping tasks
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.haunts.models import Haunt, Folder
from apps.rss.models import RSSItem
from apps.scraping.tasks import scrape_haunts_by_interval, scrape_haunt, should_skip_scrape
from apps.scraping.services import ScrapingError

User = get_user_model()


class ScrapingTasksTest(TestCase):
    """Test cases for Celery scraping tasks"""

    def setUp(self):
        """Set up test fixtures"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create test haunt
        self.haunt = Haunt.objects.create(
            owner=self.user,
            name='Test Haunt',
            url='https://example.com',
            description='Test description',
            config={
                'selectors': {
                    'status': 'css:.status'
                },
                'normalization': {
                    'status': {
                        'type': 'text',
                        'transform': 'lowercase'
                    }
                },
                'truthy_values': {
                    'status': ['open', 'available']
                }
            },
            current_state={},
            alert_mode='on_change',
            scrape_interval=15,
            is_active=True
        )

    def test_should_skip_scrape_never_scraped(self):
        """Test should_skip_scrape with haunt that was never scraped"""
        self.haunt.last_scraped_at = None
        self.haunt.save()

        should_skip = should_skip_scrape(self.haunt, 15)

        self.assertFalse(should_skip)

    def test_should_skip_scrape_recently_scraped(self):
        """Test should_skip_scrape with recently scraped haunt"""
        self.haunt.last_scraped_at = timezone.now() - timedelta(minutes=5)
        self.haunt.save()

        should_skip = should_skip_scrape(self.haunt, 15)

        self.assertTrue(should_skip)

    def test_should_skip_scrape_ready_to_scrape(self):
        """Test should_skip_scrape with haunt ready to be scraped"""
        self.haunt.last_scraped_at = timezone.now() - timedelta(minutes=20)
        self.haunt.save()

        should_skip = should_skip_scrape(self.haunt, 15)

        self.assertFalse(should_skip)

    def test_scrape_haunts_by_interval_no_haunts(self):
        """Test scrape_haunts_by_interval with no matching haunts"""
        # Make haunt inactive
        self.haunt.is_active = False
        self.haunt.save()

        result = scrape_haunts_by_interval(15)

        self.assertEqual(result['total'], 0)
        self.assertEqual(result['success'], 0)
        self.assertEqual(result['failed'], 0)
        self.assertEqual(result['skipped'], 0)

    @patch('apps.scraping.tasks.scrape_haunt.delay')
    def test_scrape_haunts_by_interval_with_haunts(self, mock_scrape):
        """Test scrape_haunts_by_interval with matching haunts"""
        # Create additional haunts
        Haunt.objects.create(
            owner=self.user,
            name='Test Haunt 2',
            url='https://example2.com',
            config={'selectors': {'status': 'css:.status'}, 'normalization': {}, 'truthy_values': {}},
            scrape_interval=15,
            is_active=True
        )

        result = scrape_haunts_by_interval(15)

        self.assertEqual(result['total'], 2)
        self.assertEqual(result['success'], 2)
        self.assertEqual(result['failed'], 0)
        self.assertEqual(mock_scrape.call_count, 2)

    @patch('apps.scraping.tasks.scrape_haunt.delay')
    def test_scrape_haunts_by_interval_skips_recent(self, mock_scrape):
        """Test scrape_haunts_by_interval skips recently scraped haunts"""
        # Set last scraped time to recent
        self.haunt.last_scraped_at = timezone.now() - timedelta(minutes=5)
        self.haunt.save()

        result = scrape_haunts_by_interval(15)

        self.assertEqual(result['total'], 1)
        self.assertEqual(result['success'], 0)
        self.assertEqual(result['skipped'], 1)
        self.assertEqual(mock_scrape.call_count, 0)

    @patch('apps.scraping.services.ScrapingService.scrape_url')
    def test_scrape_haunt_success_no_changes(self, mock_scrape_url):
        """Test scrape_haunt with successful scrape and no changes"""
        # Mock scraping to return same state
        mock_scrape_url.return_value = {}

        result = scrape_haunt(str(self.haunt.id))

        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['haunt_id'], str(self.haunt.id))
        self.assertFalse(result['has_changes'])
        self.assertEqual(result['changes_count'], 0)
        self.assertFalse(result['rss_item_created'])

        # Verify haunt was updated
        self.haunt.refresh_from_db()
        self.assertIsNotNone(self.haunt.last_scraped_at)
        self.assertEqual(self.haunt.error_count, 0)

    @patch('apps.scraping.services.ScrapingService.scrape_url')
    def test_scrape_haunt_success_with_changes(self, mock_scrape_url):
        """Test scrape_haunt with successful scrape and changes detected"""
        # Set initial state
        self.haunt.current_state = {'status': 'closed'}
        self.haunt.save()

        # Mock scraping to return new state
        mock_scrape_url.return_value = {'status': 'open'}

        result = scrape_haunt(str(self.haunt.id))

        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['has_changes'])
        self.assertEqual(result['changes_count'], 1)
        self.assertTrue(result['rss_item_created'])

        # Verify haunt state was updated
        self.haunt.refresh_from_db()
        self.assertEqual(self.haunt.current_state, {'status': 'open'})

        # Verify RSS item was created
        rss_items = RSSItem.objects.filter(haunt=self.haunt)
        self.assertEqual(rss_items.count(), 1)
        self.assertIn('status', rss_items.first().change_data)

    @patch('apps.scraping.services.ScrapingService.scrape_url')
    def test_scrape_haunt_alert_mode_once(self, mock_scrape_url):
        """Test scrape_haunt with alert_mode='once'"""
        # Set alert mode to once
        self.haunt.alert_mode = 'once'
        self.haunt.current_state = {'status': 'closed'}
        self.haunt.last_alert_state = None
        self.haunt.save()

        # Mock scraping to return truthy state
        mock_scrape_url.return_value = {'status': 'open'}

        result = scrape_haunt(str(self.haunt.id))

        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['should_alert'])

        # Verify alert state was updated
        self.haunt.refresh_from_db()
        self.assertEqual(self.haunt.last_alert_state, {'status': 'open'})

    @patch('apps.scraping.services.ScrapingService.scrape_url')
    def test_scrape_haunt_alert_mode_once_already_alerted(self, mock_scrape_url):
        """Test scrape_haunt with alert_mode='once' when already alerted"""
        # Set alert mode to once with previous alert
        self.haunt.alert_mode = 'once'
        self.haunt.current_state = {'status': 'open'}
        self.haunt.last_alert_state = {'status': 'open'}
        self.haunt.save()

        # Mock scraping to return same truthy state
        mock_scrape_url.return_value = {'status': 'open'}

        result = scrape_haunt(str(self.haunt.id))

        self.assertEqual(result['status'], 'success')
        self.assertFalse(result['should_alert'])

    @patch('apps.scraping.services.ScrapingService.scrape_url')
    def test_scrape_haunt_scraping_error(self, mock_scrape_url):
        """Test scrape_haunt with scraping error"""
        # Mock scraping to raise error
        mock_scrape_url.side_effect = ScrapingError('Test error')

        # Should raise ScrapingError to trigger retry
        with self.assertRaises(ScrapingError):
            scrape_haunt(str(self.haunt.id))

        # Verify error was tracked
        self.haunt.refresh_from_db()
        self.assertEqual(self.haunt.error_count, 1)
        self.assertIn('Test error', self.haunt.last_error)

    def test_scrape_haunt_inactive_haunt(self):
        """Test scrape_haunt with inactive haunt"""
        self.haunt.is_active = False
        self.haunt.save()

        result = scrape_haunt(str(self.haunt.id))

        self.assertEqual(result['status'], 'skipped')
        self.assertEqual(result['reason'], 'inactive')

    def test_scrape_haunt_nonexistent_haunt(self):
        """Test scrape_haunt with non-existent haunt"""
        result = scrape_haunt('00000000-0000-0000-0000-000000000000')

        self.assertEqual(result['status'], 'error')
        self.assertIn('not found', result['error'])

    @patch('apps.scraping.services.ScrapingService.scrape_url')
    def test_scrape_haunt_creates_rss_item_with_changes(self, mock_scrape_url):
        """Test that RSS item is created when changes are detected"""
        # Set initial state
        self.haunt.current_state = {'status': 'closed'}
        self.haunt.save()

        # Mock scraping to return new state
        mock_scrape_url.return_value = {'status': 'open'}

        # Verify no RSS items exist
        self.assertEqual(RSSItem.objects.filter(haunt=self.haunt).count(), 0)

        result = scrape_haunt(str(self.haunt.id))

        # Verify RSS item was created
        self.assertEqual(RSSItem.objects.filter(haunt=self.haunt).count(), 1)
        rss_item = RSSItem.objects.get(haunt=self.haunt)
        self.assertEqual(rss_item.haunt, self.haunt)
        self.assertEqual(rss_item.link, self.haunt.url)
        self.assertIn('status', rss_item.change_data)

    @patch('apps.scraping.services.ScrapingService.scrape_url')
    def test_scrape_haunt_no_rss_item_without_changes(self, mock_scrape_url):
        """Test that no RSS item is created when no changes detected"""
        # Set initial state
        self.haunt.current_state = {'status': 'open'}
        self.haunt.save()

        # Mock scraping to return same state
        mock_scrape_url.return_value = {'status': 'open'}

        result = scrape_haunt(str(self.haunt.id))

        # Verify no RSS item was created
        self.assertEqual(RSSItem.objects.filter(haunt=self.haunt).count(), 0)
        self.assertFalse(result['rss_item_created'])

    @patch('apps.scraping.services.ScrapingService.scrape_url')
    def test_scrape_haunt_resets_error_count_on_success(self, mock_scrape_url):
        """Test that error count is reset after successful scrape"""
        # Set error count
        self.haunt.error_count = 3
        self.haunt.last_error = 'Previous error'
        self.haunt.save()

        # Mock successful scrape
        mock_scrape_url.return_value = {'status': 'open'}

        result = scrape_haunt(str(self.haunt.id))

        # Verify error count was reset
        self.haunt.refresh_from_db()
        self.assertEqual(self.haunt.error_count, 0)
        self.assertEqual(self.haunt.last_error, '')
