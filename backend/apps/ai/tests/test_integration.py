"""
Integration tests for AI summary generation in scraping workflow
"""
from unittest.mock import patch, Mock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.haunts.models import Haunt
from apps.rss.models import RSSItem
from apps.scraping.tasks import scrape_haunt
from apps.ai.tasks import generate_summary_async

User = get_user_model()


class AISummaryIntegrationTest(TestCase):
    """Test cases for AI summary generation integration with scraping workflow"""

    def setUp(self):
        """Set up test fixtures"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create test haunt with AI summary enabled
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
            current_state={'status': 'closed'},
            alert_mode='on_change',
            scrape_interval=15,
            is_active=True,
            enable_ai_summary=True
        )

    @patch('apps.ai.tasks.generate_summary_async.delay')
    @patch('apps.scraping.services.ScrapingService.scrape_url')
    def test_scrape_haunt_queues_ai_summary_when_enabled(self, mock_scrape_url, mock_summary_task):
        """Test that AI summary generation is queued when changes detected and AI enabled"""
        # Mock scraping to return new state
        mock_scrape_url.return_value = {'status': 'open'}

        result = scrape_haunt(str(self.haunt.id))

        # Verify scrape was successful
        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['has_changes'])
        self.assertTrue(result['rss_item_created'])

        # Verify AI summary task was queued
        self.assertEqual(mock_summary_task.call_count, 1)

        # Verify task was called with correct arguments
        call_args = mock_summary_task.call_args[0]
        rss_item_id = call_args[0]
        old_state = call_args[1]
        new_state = call_args[2]

        self.assertIsNotNone(rss_item_id)
        self.assertEqual(old_state, {'status': 'closed'})
        self.assertEqual(new_state, {'status': 'open'})

    @patch('apps.ai.tasks.generate_summary_async.delay')
    @patch('apps.scraping.services.ScrapingService.scrape_url')
    def test_scrape_haunt_skips_ai_summary_when_disabled(self, mock_scrape_url, mock_summary_task):
        """Test that AI summary generation is skipped when disabled"""
        # Disable AI summary
        self.haunt.enable_ai_summary = False
        self.haunt.save()

        # Mock scraping to return new state
        mock_scrape_url.return_value = {'status': 'open'}

        result = scrape_haunt(str(self.haunt.id))

        # Verify scrape was successful
        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['has_changes'])
        self.assertTrue(result['rss_item_created'])

        # Verify AI summary task was NOT queued
        self.assertEqual(mock_summary_task.call_count, 0)

    @patch('apps.ai.tasks.generate_summary_async.delay')
    @patch('apps.scraping.services.ScrapingService.scrape_url')
    def test_scrape_haunt_skips_ai_summary_when_no_changes(self, mock_scrape_url, mock_summary_task):
        """Test that AI summary generation is skipped when no changes detected"""
        # Mock scraping to return same state
        mock_scrape_url.return_value = {'status': 'closed'}

        result = scrape_haunt(str(self.haunt.id))

        # Verify scrape was successful but no changes
        self.assertEqual(result['status'], 'success')
        self.assertFalse(result['has_changes'])
        self.assertFalse(result['rss_item_created'])

        # Verify AI summary task was NOT queued
        self.assertEqual(mock_summary_task.call_count, 0)

    @patch('apps.ai.services.AIConfigService.generate_summary')
    @patch('apps.ai.services.AIConfigService.is_available')
    def test_generate_summary_async_success(self, mock_is_available, mock_generate_summary):
        """Test successful async AI summary generation"""
        # Create RSS item
        rss_item = RSSItem.objects.create(
            haunt=self.haunt,
            title='Test Change',
            description='status: closed → open',
            link=self.haunt.url,
            pub_date=timezone.now(),
            change_data={'status': {'old': 'closed', 'new': 'open'}},
            ai_summary=''
        )

        # Mock AI service
        mock_is_available.return_value = True
        mock_generate_summary.return_value = 'Status changed from closed to open'

        # Call async task
        old_state = {'status': 'closed'}
        new_state = {'status': 'open'}
        result = generate_summary_async(str(rss_item.id), old_state, new_state)

        # Verify result
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['rss_item_id'], str(rss_item.id))
        self.assertEqual(result['summary'], 'Status changed from closed to open')

        # Verify RSS item was updated
        rss_item.refresh_from_db()
        self.assertEqual(rss_item.ai_summary, 'Status changed from closed to open')

        # Verify AI service was called
        mock_generate_summary.assert_called_once_with(old_state, new_state)

    @patch('apps.ai.services.AIConfigService.is_available')
    def test_generate_summary_async_ai_not_available(self, mock_is_available):
        """Test async summary generation when AI service not available"""
        # Create RSS item
        rss_item = RSSItem.objects.create(
            haunt=self.haunt,
            title='Test Change',
            description='status: closed → open',
            link=self.haunt.url,
            pub_date=timezone.now(),
            change_data={'status': {'old': 'closed', 'new': 'open'}},
            ai_summary=''
        )

        # Mock AI service not available
        mock_is_available.return_value = False

        # Call async task
        old_state = {'status': 'closed'}
        new_state = {'status': 'open'}
        result = generate_summary_async(str(rss_item.id), old_state, new_state)

        # Verify result
        self.assertEqual(result['status'], 'skipped')
        self.assertEqual(result['reason'], 'AI service not available')

        # Verify RSS item was NOT updated
        rss_item.refresh_from_db()
        self.assertEqual(rss_item.ai_summary, '')

    def test_generate_summary_async_rss_item_not_found(self):
        """Test async summary generation with non-existent RSS item"""
        # Call async task with non-existent ID
        old_state = {'status': 'closed'}
        new_state = {'status': 'open'}
        result = generate_summary_async(
            '00000000-0000-0000-0000-000000000000',
            old_state,
            new_state
        )

        # Verify result
        self.assertEqual(result['status'], 'error')
        self.assertIn('not found', result['error'])

    @patch('apps.ai.services.AIConfigService.generate_summary')
    @patch('apps.ai.services.AIConfigService.is_available')
    def test_generate_summary_async_invalidates_cache(self, mock_is_available, mock_generate_summary):
        """Test that async summary generation invalidates RSS feed cache"""
        # Create RSS item
        rss_item = RSSItem.objects.create(
            haunt=self.haunt,
            title='Test Change',
            description='status: closed → open',
            link=self.haunt.url,
            pub_date=timezone.now(),
            change_data={'status': {'old': 'closed', 'new': 'open'}},
            ai_summary=''
        )

        # Mock AI service
        mock_is_available.return_value = True
        mock_generate_summary.return_value = 'Status changed from closed to open'

        # Mock cache invalidation
        with patch('apps.rss.services.RSSService.invalidate_feed_cache') as mock_invalidate:
            # Call async task
            old_state = {'status': 'closed'}
            new_state = {'status': 'open'}
            result = generate_summary_async(str(rss_item.id), old_state, new_state)

            # Verify cache was invalidated
            mock_invalidate.assert_called_once_with(self.haunt)

    @patch('apps.ai.services.AIConfigService.generate_summary')
    @patch('apps.ai.services.AIConfigService.is_available')
    def test_generate_summary_async_with_multiple_changes(self, mock_is_available, mock_generate_summary):
        """Test async summary generation with multiple field changes"""
        # Create RSS item with multiple changes
        rss_item = RSSItem.objects.create(
            haunt=self.haunt,
            title='Test Change',
            description='Multiple changes',
            link=self.haunt.url,
            pub_date=timezone.now(),
            change_data={
                'status': {'old': 'closed', 'new': 'open'},
                'deadline': {'old': '2024-01-01', 'new': '2024-02-01'}
            },
            ai_summary=''
        )

        # Mock AI service
        mock_is_available.return_value = True
        mock_generate_summary.return_value = 'Status changed to open and deadline extended to February'

        # Call async task
        old_state = {'status': 'closed', 'deadline': '2024-01-01'}
        new_state = {'status': 'open', 'deadline': '2024-02-01'}
        result = generate_summary_async(str(rss_item.id), old_state, new_state)

        # Verify result
        self.assertEqual(result['status'], 'success')
        self.assertIn('February', result['summary'])

        # Verify RSS item was updated
        rss_item.refresh_from_db()
        self.assertIn('February', rss_item.ai_summary)

    @patch('apps.ai.services.AIConfigService.generate_summary')
    @patch('apps.ai.services.AIConfigService.is_available')
    def test_scraping_workflow_end_to_end_with_ai_summary(self, mock_is_available, mock_generate_summary):
        """Test complete scraping workflow with AI summary generation"""
        # Mock AI service
        mock_is_available.return_value = True
        mock_generate_summary.return_value = 'Application status changed from closed to open'

        # Mock scraping
        with patch('apps.scraping.services.ScrapingService.scrape_url') as mock_scrape_url:
            mock_scrape_url.return_value = {'status': 'open'}

            # Run scrape task (this will queue the summary task)
            with patch('apps.ai.tasks.generate_summary_async.delay') as mock_summary_task:
                result = scrape_haunt(str(self.haunt.id))

                # Verify scrape was successful
                self.assertEqual(result['status'], 'success')
                self.assertTrue(result['has_changes'])
                self.assertTrue(result['rss_item_created'])

                # Verify summary task was queued
                self.assertEqual(mock_summary_task.call_count, 1)

                # Get the RSS item that was created
                rss_item = RSSItem.objects.get(haunt=self.haunt)

                # Manually run the summary task (simulating Celery execution)
                summary_result = generate_summary_async(
                    str(rss_item.id),
                    {'status': 'closed'},
                    {'status': 'open'}
                )

                # Verify summary was generated
                self.assertEqual(summary_result['status'], 'success')

                # Verify RSS item has AI summary
                rss_item.refresh_from_db()
                self.assertEqual(rss_item.ai_summary, 'Application status changed from closed to open')
