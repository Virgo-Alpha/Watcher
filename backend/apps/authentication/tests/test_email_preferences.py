"""
Unit tests for user email notification preferences.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class UserEmailPreferencesTestCase(TestCase):
    """Test user email notification preferences."""
    
    def test_user_email_notifications_enabled_by_default(self):
        """Test that email notifications are enabled by default."""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='pass123'
        )
        
        self.assertTrue(user.email_notifications_enabled)
    
    def test_user_can_disable_email_notifications(self):
        """Test that user can disable email notifications."""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='pass123',
            email_notifications_enabled=False
        )
        
        self.assertFalse(user.email_notifications_enabled)
    
    def test_user_can_toggle_email_notifications(self):
        """Test that user can toggle email notifications."""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='pass123'
        )
        
        # Initially enabled
        self.assertTrue(user.email_notifications_enabled)
        
        # Disable
        user.email_notifications_enabled = False
        user.save()
        user.refresh_from_db()
        self.assertFalse(user.email_notifications_enabled)
        
        # Re-enable
        user.email_notifications_enabled = True
        user.save()
        user.refresh_from_db()
        self.assertTrue(user.email_notifications_enabled)
    
    def test_email_notifications_field_persists(self):
        """Test that email notifications preference persists in database."""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='pass123',
            email_notifications_enabled=False
        )
        
        # Retrieve from database
        retrieved_user = User.objects.get(email='test@example.com')
        self.assertFalse(retrieved_user.email_notifications_enabled)
    
    def test_multiple_users_independent_preferences(self):
        """Test that multiple users have independent email preferences."""
        user1 = User.objects.create_user(
            email='user1@example.com',
            username='user1',
            password='pass123',
            email_notifications_enabled=True
        )
        
        user2 = User.objects.create_user(
            email='user2@example.com',
            username='user2',
            password='pass123',
            email_notifications_enabled=False
        )
        
        self.assertTrue(user1.email_notifications_enabled)
        self.assertFalse(user2.email_notifications_enabled)
        
        # Changing one doesn't affect the other
        user1.email_notifications_enabled = False
        user1.save()
        
        user2.refresh_from_db()
        self.assertFalse(user2.email_notifications_enabled)
