"""
Integration tests for AI-powered scraping workflow
"""
from unittest.mock import Mock, patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.haunts.models import Haunt
from apps.scraping.tasks import scrape_haunt
from apps.scraping.services import ChangeDetectionService
import json

User = get_user_model()


class AIScrapingIntegrationTestCase(TestCase):
    """Test complete scraping workflow with AI alert decisions"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

        self.haunt = Haunt.objects.create(
            owner=self.user,
            name='Test Fellowship',
            url='https://example.com/fellowship',
            description='Alert me when fellowship applications are open',
            config={
                'selectors': {
                    'status': 'css:.application-status'
                },
                'normalization': {
                    'status': {
                        'type': 'text',
                        'transform': 'lowercase',
                        'strip': True
                    }
                }
            },
            current_state={},
            scrape_interval=60,
            is_active=True,
            enable_ai_summary=True
        )

    @patch('apps.scraping.services.ScrapingService.scrape_url')
    @patch('apps.ai.services.AIConfigService.evaluate_alert_decision')
    def test_scrape_with_ai_alert_decision_should_alert(self, mock_ai_eval, mock_scrape):
        """Test complete scraping workflow when AI decides to alert"""
        # Mock scraping result
        mock_scrape.return_value = {
            'status': 'now accepting applications'
        }

        # Mock AI evaluation - should alert
        mock_ai_eval.return_value = {
            'should_alert': True,
            'reason': 'Applications are now open',
            'confidence': 0.95,
            'summary': 'Fellowship applications are now open for Spring 2026.'
        }

        # Execute scrape
        result = scrape_haunt(str(self.haunt.id))

        # Verify scraping was called
        mock_scrape.assert_called_once()

        # Verify AI evaluation was called with correct parameters
        mock_ai_eval.assert_called_once()
        call_args = mock_ai_eval.call_args
        self.assertEqual(call_args[1]['user_description'], self.haunt.description)
        self.assertEqual(call_args[1]['old_state'], {})
        self.assertEqual(call_args[1]['new_state'], {'status': 'now accepting applications'})

        # Verify result
        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['has_changes'])
        self.assertTrue(result['should_alert'])
        self.assertTrue(result['rss_item_created'])

        # Verify haunt state was updated
        self.haunt.refresh_from_db()
        self.assertEqual(self.haunt.current_state, {'status': 'now accepting applications'})
        self.assertEqual(self.haunt.last_alert_state, {'status': 'now accepting applications'})
        self.assertIsNotNone(self.haunt.last_scraped_at)

    @patch('apps.scraping.services.ScrapingService.scrape_url')
    @patch('apps.ai.services.AIConfigService.evaluate_alert_decision')
    def test_scrape_with_ai_alert_decision_should_not_alert(self, mock_ai_eval, mock_scrape):
        """Test complete scraping workflow when AI decides NOT to alert"""
        # Set initial state
        self.haunt.current_state = {'status': 'applications closed'}
        self.haunt.save()

        # Mock scraping result - minor change
        mock_scrape.return_value = {
            'status': 'applications closed for now'
        }

        # Mock AI evaluation - should NOT alert
        mock_ai_eval.return_value = {
            'should_alert': False,
            'reason': 'Minor wording change, applications still closed',
            'confidence': 0.88,
            'summary': 'Status wording updated but applications remain closed.'
        }

        # Execute scrape
        result = scrape_haunt(str(self.haunt.id))

        # Verify AI evaluation was called
        mock_ai_eval.assert_called_once()

        # Verify result
        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['has_changes'])
        self.assertFalse(result['should_alert'])
        self.assertFalse(result['rss_item_created'])

        # Verify haunt state was updated but alert state unchanged (no alert sent)
        self.haunt.refresh_from_db()
        self.assertEqual(self.haunt.current_state, {'status': 'applications closed for now'})
        # Alert state should remain None since no alert was sent
        self.assertIsNone(self.haunt.last_alert_state)

    @patch('apps.scraping.services.ScrapingService.scrape_url')
    @patch('apps.ai.services.AIConfigService.evaluate_alert_decision')
    def test_scrape_no_changes_no_ai_call(self, mock_ai_eval, mock_scrape):
        """Test that AI is not called when there are no changes"""
        # Set initial state
        self.haunt.current_state = {'status': 'applications closed'}
        self.haunt.save()

        # Mock scraping result - same as before
        mock_scrape.return_value = {
            'status': 'applications closed'
        }

        # Execute scrape
        result = scrape_haunt(str(self.haunt.id))

        # Verify AI evaluation was NOT called (no changes)
        mock_ai_eval.assert_not_called()

        # Verify result
        self.assertEqual(result['status'], 'success')
        self.assertFalse(result['has_changes'])
        self.assertFalse(result['should_alert'])
        self.assertFalse(result['rss_item_created'])

    @patch('apps.scraping.services.ScrapingService.scrape_url')
    @patch('apps.ai.services.AIConfigService.evaluate_alert_decision')
    def test_scrape_with_ai_summary_disabled(self, mock_ai_eval, mock_scrape):
        """Test scraping when AI summary is disabled"""
        # Disable AI summary
        self.haunt.enable_ai_summary = False
        self.haunt.save()

        # Mock scraping result
        mock_scrape.return_value = {
            'status': 'now accepting applications'
        }

        # Mock AI evaluation
        mock_ai_eval.return_value = {
            'should_alert': True,
            'reason': 'Applications are now open',
            'confidence': 0.95,
            'summary': 'Fellowship applications are now open.'
        }

        # Execute scrape
        result = scrape_haunt(str(self.haunt.id))

        # Verify AI was still called for alert decision
        mock_ai_eval.assert_called_once()

        # Verify result
        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['should_alert'])

    @patch('apps.scraping.services.ScrapingService.scrape_url')
    @patch('apps.ai.services.AIConfigService.evaluate_alert_decision')
    def test_scrape_with_multiple_field_changes(self, mock_ai_eval, mock_scrape):
        """Test scraping with multiple fields changing"""
        # Set initial state
        self.haunt.current_state = {
            'status': 'closed',
            'deadline': None
        }
        self.haunt.config['selectors']['deadline'] = 'css:.deadline'
        self.haunt.config['normalization']['deadline'] = {
            'type': 'text',
            'strip': True
        }
        self.haunt.save()

        # Mock scraping result - multiple changes
        mock_scrape.return_value = {
            'status': 'open',
            'deadline': 'March 15, 2026'
        }

        # Mock AI evaluation
        mock_ai_eval.return_value = {
            'should_alert': True,
            'reason': 'Applications opened with new deadline',
            'confidence': 0.97,
            'summary': 'Applications opened with deadline of March 15, 2026.'
        }

        # Execute scrape
        result = scrape_haunt(str(self.haunt.id))

        # Verify AI was called with all changes
        call_args = mock_ai_eval.call_args
        changes = call_args[1]['changes']
        self.assertIn('status', changes)
        self.assertIn('deadline', changes)
        self.assertEqual(changes['status']['new'], 'open')
        self.assertEqual(changes['deadline']['new'], 'March 15, 2026')

        # Verify result
        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['should_alert'])
        self.assertEqual(result['changes_count'], 2)

    @patch('apps.scraping.services.ScrapingService.scrape_url')
    @patch('apps.ai.services.AIConfigService.evaluate_alert_decision')
    def test_scrape_with_ai_fallback(self, mock_ai_eval, mock_scrape):
        """Test scraping when AI service falls back to simple detection"""
        # Mock scraping result
        mock_scrape.return_value = {
            'status': 'now accepting applications'
        }

        # Mock AI evaluation - fallback response
        mock_ai_eval.return_value = {
            'should_alert': True,
            'reason': 'AI unavailable, alerting on any change',
            'confidence': 0.5,
            'summary': 'status changed from None to now accepting applications'
        }

        # Execute scrape
        result = scrape_haunt(str(self.haunt.id))

        # Verify result - should still work with fallback
        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['should_alert'])
        self.assertTrue(result['rss_item_created'])


class ChangeDetectionServiceTestCase(TestCase):
    """Test simplified change detection service"""

    def setUp(self):
        """Set up test fixtures"""
        self.service = ChangeDetectionService()

    def test_detect_changes_first_scrape(self):
        """Test change detection on first scrape (no old state)"""
        old_state = {}
        new_state = {'status': 'open', 'deadline': 'March 15'}

        has_changes, changes = self.service.detect_changes(old_state, new_state)

        self.assertTrue(has_changes)
        self.assertEqual(len(changes), 2)
        self.assertIn('status', changes)
        self.assertIn('deadline', changes)
        self.assertIsNone(changes['status']['old'])
        self.assertEqual(changes['status']['new'], 'open')

    def test_detect_changes_with_changes(self):
        """Test change detection when values change"""
        old_state = {'status': 'closed', 'deadline': None}
        new_state = {'status': 'open', 'deadline': 'March 15'}

        has_changes, changes = self.service.detect_changes(old_state, new_state)

        self.assertTrue(has_changes)
        self.assertEqual(len(changes), 2)
        self.assertEqual(changes['status']['old'], 'closed')
        self.assertEqual(changes['status']['new'], 'open')
        self.assertIsNone(changes['deadline']['old'])
        self.assertEqual(changes['deadline']['new'], 'March 15')

    def test_detect_changes_no_changes(self):
        """Test change detection when nothing changes"""
        old_state = {'status': 'open', 'deadline': 'March 15'}
        new_state = {'status': 'open', 'deadline': 'March 15'}

        has_changes, changes = self.service.detect_changes(old_state, new_state)

        self.assertFalse(has_changes)
        self.assertEqual(len(changes), 0)

    def test_detect_changes_partial_changes(self):
        """Test change detection when only some fields change"""
        old_state = {'status': 'open', 'deadline': 'March 15', 'batch': 'Spring'}
        new_state = {'status': 'open', 'deadline': 'March 20', 'batch': 'Spring'}

        has_changes, changes = self.service.detect_changes(old_state, new_state)

        self.assertTrue(has_changes)
        self.assertEqual(len(changes), 1)
        self.assertIn('deadline', changes)
        self.assertNotIn('status', changes)
        self.assertNotIn('batch', changes)

    def test_detect_changes_field_removed(self):
        """Test change detection when a field is removed"""
        old_state = {'status': 'open', 'deadline': 'March 15'}
        new_state = {'status': 'open'}

        has_changes, changes = self.service.detect_changes(old_state, new_state)

        self.assertTrue(has_changes)
        self.assertEqual(len(changes), 1)
        self.assertIn('deadline', changes)
        self.assertEqual(changes['deadline']['old'], 'March 15')
        self.assertIsNone(changes['deadline']['new'])

    def test_detect_changes_field_added(self):
        """Test change detection when a new field is added"""
        old_state = {'status': 'open'}
        new_state = {'status': 'open', 'deadline': 'March 15'}

        has_changes, changes = self.service.detect_changes(old_state, new_state)

        self.assertTrue(has_changes)
        self.assertEqual(len(changes), 1)
        self.assertIn('deadline', changes)
        self.assertIsNone(changes['deadline']['old'])
        self.assertEqual(changes['deadline']['new'], 'March 15')
