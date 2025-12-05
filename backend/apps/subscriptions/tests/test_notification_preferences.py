"""
Unit tests for subscription notification preferences.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.haunts.models import Haunt
from apps.subscriptions.models import Subscription

User = get_user_model()


class SubscriptionNotificationPreferencesTestCase(TestCase):
    """Test subscription-level notification preferences."""
    
    def setUp(self):
        """Set up test data."""
        self.owner = User.objects.create_user(
            email='owner@example.com',
            username='owner',
            password='pass123'
        )
        
        self.subscriber = User.objects.create_user(
            email='subscriber@example.com',
            username='subscriber',
            password='pass123'
        )
        
        self.haunt = Haunt.objects.create(
            owner=self.owner,
            name='Test Haunt',
            url='https://example.com',
            description='Test haunt',
            is_public=True,
            config={'selectors': {}, 'normalization': {}}
        )
    
    def test_subscription_notifications_enabled_by_default(self):
        """Test that subscription notifications are enabled by default."""
        subscription = Subscription.objects.create(
            user=self.subscriber,
            haunt=self.haunt
        )
        
        self.assertTrue(subscription.notifications_enabled)
    
    def test_subscription_can_disable_notifications(self):
        """Test that user can disable notifications for specific subscription."""
        subscription = Subscription.objects.create(
            user=self.subscriber,
            haunt=self.haunt,
            notifications_enabled=False
        )
        
        self.assertFalse(subscription.notifications_enabled)
    
    def test_subscription_can_toggle_notifications(self):
        """Test that user can toggle notifications for subscription."""
        subscription = Subscription.objects.create(
            user=self.subscriber,
            haunt=self.haunt
        )
        
        # Initially enabled
        self.assertTrue(subscription.notifications_enabled)
        
        # Disable
        subscription.notifications_enabled = False
        subscription.save()
        subscription.refresh_from_db()
        self.assertFalse(subscription.notifications_enabled)
        
        # Re-enable
        subscription.notifications_enabled = True
        subscription.save()
        subscription.refresh_from_db()
        self.assertTrue(subscription.notifications_enabled)
    
    def test_multiple_subscriptions_independent_preferences(self):
        """Test that user can have different preferences for different haunts."""
        haunt2 = Haunt.objects.create(
            owner=self.owner,
            name='Test Haunt 2',
            url='https://example2.com',
            description='Test haunt 2',
            is_public=True,
            config={'selectors': {}, 'normalization': {}}
        )
        
        subscription1 = Subscription.objects.create(
            user=self.subscriber,
            haunt=self.haunt,
            notifications_enabled=True
        )
        
        subscription2 = Subscription.objects.create(
            user=self.subscriber,
            haunt=haunt2,
            notifications_enabled=False
        )
        
        self.assertTrue(subscription1.notifications_enabled)
        self.assertFalse(subscription2.notifications_enabled)
    
    def test_subscription_notifications_persist(self):
        """Test that subscription notification preferences persist."""
        subscription = Subscription.objects.create(
            user=self.subscriber,
            haunt=self.haunt,
            notifications_enabled=False
        )
        
        # Retrieve from database
        retrieved = Subscription.objects.get(
            user=self.subscriber,
            haunt=self.haunt
        )
        self.assertFalse(retrieved.notifications_enabled)
    
    def test_user_level_overrides_subscription_level(self):
        """Test that user-level disabled overrides subscription-level enabled."""
        # This is tested in email service, but document the behavior here
        self.subscriber.email_notifications_enabled = False
        self.subscriber.save()
        
        subscription = Subscription.objects.create(
            user=self.subscriber,
            haunt=self.haunt,
            notifications_enabled=True  # Enabled at subscription level
        )
        
        # User-level setting should take precedence
        # (This is enforced in EmailNotificationService)
        self.assertFalse(self.subscriber.email_notifications_enabled)
        self.assertTrue(subscription.notifications_enabled)


class SubscriptionNotificationFilteringTestCase(TestCase):
    """Test filtering subscriptions by notification preferences."""
    
    def setUp(self):
        """Set up test data."""
        self.owner = User.objects.create_user(
            email='owner@example.com',
            username='owner',
            password='pass123'
        )
        
        self.haunt = Haunt.objects.create(
            owner=self.owner,
            name='Test Haunt',
            url='https://example.com',
            description='Test haunt',
            is_public=True,
            config={'selectors': {}, 'normalization': {}}
        )
        
        # Create users with different preferences
        self.user_enabled = User.objects.create_user(
            email='enabled@example.com',
            username='enabled',
            password='pass123',
            email_notifications_enabled=True
        )
        
        self.user_disabled = User.objects.create_user(
            email='disabled@example.com',
            username='disabled',
            password='pass123',
            email_notifications_enabled=False
        )
    
    def test_filter_subscriptions_with_notifications_enabled(self):
        """Test filtering subscriptions with notifications enabled."""
        # Create subscriptions
        sub1 = Subscription.objects.create(
            user=self.user_enabled,
            haunt=self.haunt,
            notifications_enabled=True
        )
        
        sub2 = Subscription.objects.create(
            user=self.user_disabled,
            haunt=self.haunt,
            notifications_enabled=True
        )
        
        # Filter for notification-enabled subscriptions
        enabled_subs = Subscription.objects.filter(
            haunt=self.haunt,
            notifications_enabled=True,
            user__email_notifications_enabled=True
        )
        
        self.assertEqual(enabled_subs.count(), 1)
        self.assertIn(sub1, enabled_subs)
        self.assertNotIn(sub2, enabled_subs)
    
    def test_filter_excludes_subscription_level_disabled(self):
        """Test filtering excludes subscription-level disabled."""
        # Create a second haunt for the second subscription
        haunt2 = Haunt.objects.create(
            owner=self.owner,
            name='Test Haunt 2',
            url='https://example2.com',
            description='Test haunt 2',
            is_public=True,
            config={'selectors': {}, 'normalization': {}}
        )
        
        sub1 = Subscription.objects.create(
            user=self.user_enabled,
            haunt=self.haunt,
            notifications_enabled=True
        )
        
        sub2 = Subscription.objects.create(
            user=self.user_enabled,
            haunt=haunt2,
            notifications_enabled=False
        )
        
        # Filter for notification-enabled subscriptions for user_enabled
        enabled_subs = Subscription.objects.filter(
            user=self.user_enabled,
            notifications_enabled=True,
            user__email_notifications_enabled=True
        )
        
        self.assertEqual(enabled_subs.count(), 1)
        self.assertIn(sub1, enabled_subs)
        self.assertNotIn(sub2, enabled_subs)
