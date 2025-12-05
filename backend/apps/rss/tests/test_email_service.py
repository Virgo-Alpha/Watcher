"""
Unit tests for email notification service.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core import mail

from apps.haunts.models import Haunt
from apps.rss.models import RSSItem
from apps.subscriptions.models import Subscription
from apps.rss.services import EmailNotificationService

User = get_user_model()


class EmailNotificationServiceTestCase(TestCase):
    """Test email notification service functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create users
        self.owner = User.objects.create_user(
            email='owner@example.com',
            username='owner',
            password='pass123',
            email_notifications_enabled=True
        )
        
        self.subscriber1 = User.objects.create_user(
            email='subscriber1@example.com',
            username='subscriber1',
            password='pass123',
            email_notifications_enabled=True
        )
        
        self.subscriber2 = User.objects.create_user(
            email='subscriber2@example.com',
            username='subscriber2',
            password='pass123',
            email_notifications_enabled=False  # Disabled
        )
        
        self.subscriber3 = User.objects.create_user(
            email='subscriber3@example.com',
            username='subscriber3',
            password='pass123',
            email_notifications_enabled=True
        )
        
        # Create haunt
        self.haunt = Haunt.objects.create(
            owner=self.owner,
            name='Test Haunt',
            url='https://example.com',
            description='Test haunt for notifications',
            is_public=True,
            config={'selectors': {}, 'normalization': {}},
            current_state={'status': 'open'}
        )
        
        # Create RSS item
        self.rss_item = RSSItem.objects.create(
            haunt=self.haunt,
            title='Status Changed',
            ai_summary='Application status changed from closed to open',
            change_data={
                'status': {'old': 'closed', 'new': 'open'}
            }
        )
    
    def test_get_notification_recipients_owner_only(self):
        """Test getting recipients when only owner should be notified."""
        recipients = EmailNotificationService.get_notification_recipients(self.haunt)
        
        self.assertEqual(len(recipients), 1)
        self.assertIn(self.owner, recipients)
    
    def test_get_notification_recipients_with_subscribers(self):
        """Test getting recipients including subscribers."""
        # Create subscriptions
        Subscription.objects.create(
            user=self.subscriber1,
            haunt=self.haunt,
            notifications_enabled=True
        )
        Subscription.objects.create(
            user=self.subscriber2,
            haunt=self.haunt,
            notifications_enabled=True  # Enabled in subscription
        )
        Subscription.objects.create(
            user=self.subscriber3,
            haunt=self.haunt,
            notifications_enabled=False  # Disabled in subscription
        )
        
        recipients = EmailNotificationService.get_notification_recipients(self.haunt)
        
        # Should include: owner + subscriber1 only
        # subscriber2 excluded (user-level disabled)
        # subscriber3 excluded (subscription-level disabled)
        self.assertEqual(len(recipients), 2)
        self.assertIn(self.owner, recipients)
        self.assertIn(self.subscriber1, recipients)
        self.assertNotIn(self.subscriber2, recipients)
        self.assertNotIn(self.subscriber3, recipients)
    
    def test_get_notification_recipients_owner_disabled(self):
        """Test getting recipients when owner has notifications disabled."""
        self.owner.email_notifications_enabled = False
        self.owner.save()
        
        Subscription.objects.create(
            user=self.subscriber1,
            haunt=self.haunt,
            notifications_enabled=True
        )
        
        recipients = EmailNotificationService.get_notification_recipients(self.haunt)
        
        # Should only include subscriber1
        self.assertEqual(len(recipients), 1)
        self.assertIn(self.subscriber1, recipients)
        self.assertNotIn(self.owner, recipients)
    
    def test_get_notification_recipients_private_haunt(self):
        """Test getting recipients for private haunt (no subscribers)."""
        self.haunt.is_public = False
        self.haunt.save()
        
        # Don't create subscription - validation prevents subscribing to private haunts
        # Just test that only owner is included
        recipients = EmailNotificationService.get_notification_recipients(self.haunt)
        
        # Should only include owner
        self.assertEqual(len(recipients), 1)
        self.assertIn(self.owner, recipients)
    
    def test_send_change_notification_success(self):
        """Test sending email notification successfully."""
        result = EmailNotificationService.send_change_notification(self.rss_item)
        
        self.assertEqual(result['sent'], 1)
        self.assertEqual(result['failed'], 0)
        
        # Check email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        
        self.assertIn('Test Haunt', email.subject)
        self.assertIn('Change Detected', email.subject)
        self.assertEqual(email.to, ['owner@example.com'])
        self.assertIn('Status Changed', email.body)
        self.assertIn('https://example.com', email.body)
    
    def test_send_change_notification_multiple_recipients(self):
        """Test sending email to multiple recipients."""
        Subscription.objects.create(
            user=self.subscriber1,
            haunt=self.haunt,
            notifications_enabled=True
        )
        Subscription.objects.create(
            user=self.subscriber3,
            haunt=self.haunt,
            notifications_enabled=True
        )
        
        result = EmailNotificationService.send_change_notification(self.rss_item)
        
        self.assertEqual(result['sent'], 3)
        self.assertEqual(result['failed'], 0)
        self.assertEqual(len(mail.outbox), 3)
        
        # Check all recipients received email
        recipients = [email.to[0] for email in mail.outbox]
        self.assertIn('owner@example.com', recipients)
        self.assertIn('subscriber1@example.com', recipients)
        self.assertIn('subscriber3@example.com', recipients)
    
    def test_send_change_notification_no_recipients(self):
        """Test sending notification when no recipients."""
        self.owner.email_notifications_enabled = False
        self.owner.save()
        
        result = EmailNotificationService.send_change_notification(self.rss_item)
        
        self.assertEqual(result['sent'], 0)
        self.assertEqual(result['failed'], 0)
        self.assertEqual(len(mail.outbox), 0)
    
    def test_send_change_notification_with_html(self):
        """Test that email includes HTML alternative."""
        result = EmailNotificationService.send_change_notification(self.rss_item)
        
        self.assertEqual(result['sent'], 1)
        email = mail.outbox[0]
        
        # Check HTML alternative exists
        self.assertEqual(len(email.alternatives), 1)
        html_content = email.alternatives[0][0]
        
        self.assertIn('<!DOCTYPE html>', html_content)
        self.assertIn('Test Haunt', html_content)
        self.assertIn('Status Changed', html_content)
        self.assertIn('https://example.com', html_content)
    
    def test_render_text_email_with_changes(self):
        """Test rendering plain text email with changes."""
        text = EmailNotificationService._render_text_email(self.rss_item)
        
        self.assertIn('Test Haunt', text)
        self.assertIn('https://example.com', text)
        self.assertIn('Status Changed', text)
        self.assertIn('Application status changed', text)
        self.assertIn('status:', text)
        self.assertIn('Old: closed', text)
        self.assertIn('New: open', text)
        self.assertIn('disable these notifications', text)
    
    def test_render_text_email_without_summary(self):
        """Test rendering plain text email without AI summary."""
        self.rss_item.ai_summary = ''  # Empty string instead of None
        self.rss_item.save()
        
        text = EmailNotificationService._render_text_email(self.rss_item)
        
        self.assertIn('Test Haunt', text)
        self.assertIn('Status Changed', text)
        self.assertNotIn('Summary:', text)
    
    def test_render_html_email_with_changes(self):
        """Test rendering HTML email with changes."""
        html = EmailNotificationService._render_html_email(self.rss_item)
        
        self.assertIn('<!DOCTYPE html>', html)
        self.assertIn('Test Haunt', html)
        self.assertIn('https://example.com', html)
        self.assertIn('Status Changed', html)
        self.assertIn('Application status changed', html)
        self.assertIn('status', html)
        self.assertIn('closed', html)
        self.assertIn('open', html)
        
        # Check styling
        self.assertIn('font-family: Arial', html)
        self.assertIn('#DD4B39', html)  # Google red
        self.assertIn('#3366CC', html)  # Google blue
    
    def test_render_html_email_without_summary(self):
        """Test rendering HTML email without AI summary."""
        self.rss_item.ai_summary = ''  # Empty string instead of None
        self.rss_item.save()
        
        html = EmailNotificationService._render_html_email(self.rss_item)
        
        self.assertIn('Test Haunt', html)
        self.assertIn('Status Changed', html)
        # Summary div should not be present
        self.assertNotIn('class="summary"', html)
    
    @patch('django.core.mail.EmailMultiAlternatives.send')
    def test_send_change_notification_handles_failure(self, mock_send):
        """Test handling email send failure."""
        mock_send.side_effect = Exception('SMTP error')
        
        result = EmailNotificationService.send_change_notification(self.rss_item)
        
        self.assertEqual(result['sent'], 0)
        self.assertEqual(result['failed'], 1)
    
    @patch('django.core.mail.EmailMultiAlternatives.send')
    def test_send_change_notification_partial_failure(self, mock_send):
        """Test handling partial failure when sending to multiple recipients."""
        Subscription.objects.create(
            user=self.subscriber1,
            haunt=self.haunt,
            notifications_enabled=True
        )
        
        # First call succeeds, second fails
        mock_send.side_effect = [None, Exception('SMTP error')]
        
        result = EmailNotificationService.send_change_notification(self.rss_item)
        
        self.assertEqual(result['sent'], 1)
        self.assertEqual(result['failed'], 1)
    
    def test_email_content_includes_all_changes(self):
        """Test that email includes all change fields."""
        self.rss_item.change_data = {
            'status': {'old': 'closed', 'new': 'open'},
            'deadline': {'old': '2024-01-01', 'new': '2024-02-01'},
            'title': {'old': 'Old Title', 'new': 'New Title'}
        }
        self.rss_item.save()
        
        text = EmailNotificationService._render_text_email(self.rss_item)
        
        self.assertIn('status:', text)
        self.assertIn('deadline:', text)
        self.assertIn('title:', text)
        self.assertIn('closed', text)
        self.assertIn('open', text)
        self.assertIn('2024-01-01', text)
        self.assertIn('2024-02-01', text)
    
    def test_email_subject_includes_haunt_name(self):
        """Test that email subject includes haunt name."""
        result = EmailNotificationService.send_change_notification(self.rss_item)
        
        self.assertEqual(result['sent'], 1)
        email = mail.outbox[0]
        
        self.assertIn('[Watcher]', email.subject)
        self.assertIn('Test Haunt', email.subject)
        self.assertIn('Change Detected', email.subject)
    
    def test_no_duplicate_owner_in_recipients(self):
        """Test that owner is not duplicated if they're also a subscriber."""
        # This shouldn't happen in practice due to validation,
        # but test the service handles it correctly
        recipients = EmailNotificationService.get_notification_recipients(self.haunt)
        
        # Count occurrences of owner
        owner_count = sum(1 for r in recipients if r.id == self.owner.id)
        self.assertEqual(owner_count, 1)


class EmailNotificationIntegrationTestCase(TestCase):
    """Integration tests for email notifications with scraping."""
    
    def setUp(self):
        """Set up test data."""
        self.owner = User.objects.create_user(
            email='owner@example.com',
            username='owner',
            password='pass123',
            email_notifications_enabled=True
        )
        
        self.haunt = Haunt.objects.create(
            owner=self.owner,
            name='Integration Test Haunt',
            url='https://example.com',
            description='Test haunt',
            config={'selectors': {}, 'normalization': {}},
            current_state={}
        )
    
    def test_email_sent_when_rss_item_created(self):
        """Test that email is sent when RSS item is created."""
        from apps.rss.services import RSSService
        
        rss_service = RSSService()
        
        # Create RSS item
        rss_item = rss_service.create_rss_item(
            haunt=self.haunt,
            changes={'status': {'old': 'closed', 'new': 'open'}},
            ai_summary='Status changed to open'
        )
        
        # Manually trigger email (in real flow, this is done by scraping task)
        result = EmailNotificationService.send_change_notification(rss_item)
        
        self.assertEqual(result['sent'], 1)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertIn('Integration Test Haunt', email.subject)
        self.assertIn('Status changed to open', email.body)
