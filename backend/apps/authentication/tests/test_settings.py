"""
Test-specific settings and utilities for authentication tests.
"""
from django.test import TestCase
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class UserTestCase(TestCase):
    """Base test case class for User model tests with common utilities."""
    
    @classmethod
    def setUpClass(cls):
        """Set up class-level test data."""
        super().setUpClass()
        cls.default_user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
    
    def create_test_user(self, **kwargs):
        """Helper method to create a test user with default or custom data."""
        user_data = self.default_user_data.copy()
        user_data.update(kwargs)
        return User.objects.create_user(**user_data)
    
    def create_test_superuser(self, **kwargs):
        """Helper method to create a test superuser."""
        user_data = {
            'email': 'admin@example.com',
            'username': 'admin',
            'password': 'adminpass123'
        }
        user_data.update(kwargs)
        return User.objects.create_superuser(**user_data)
    
    def assertUserFieldsEqual(self, user, expected_data):
        """Helper method to assert user fields match expected data."""
        for field, expected_value in expected_data.items():
            if field != 'password':  # Don't check password directly
                actual_value = getattr(user, field)
                self.assertEqual(
                    actual_value, 
                    expected_value,
                    f"Field {field}: expected {expected_value}, got {actual_value}"
                )
    
    def assertUserExists(self, **lookup_kwargs):
        """Helper method to assert a user exists with given criteria."""
        self.assertTrue(
            User.objects.filter(**lookup_kwargs).exists(),
            f"User with criteria {lookup_kwargs} does not exist"
        )
    
    def assertUserDoesNotExist(self, **lookup_kwargs):
        """Helper method to assert a user does not exist with given criteria."""
        self.assertFalse(
            User.objects.filter(**lookup_kwargs).exists(),
            f"User with criteria {lookup_kwargs} should not exist"
        )


class UserModelTestSettings:
    """Test settings and constants for User model tests."""
    
    # Test data templates
    VALID_USER_DATA = {
        'email': 'valid@example.com',
        'username': 'validuser',
        'password': 'validpass123'
    }
    
    INVALID_EMAIL_FORMATS = [
        'invalid-email',
        '@example.com',
        'user@',
        'user..name@example.com',
        'user name@example.com',
        '',
        None
    ]
    
    VALID_EMAIL_FORMATS = [
        'user@example.com',
        'user.name@example.com',
        'user+tag@example.com',
        'user123@example-domain.com',
        'tëst@éxample.com'  # Unicode
    ]
    
    # Performance test thresholds
    PERFORMANCE_THRESHOLDS = {
        'user_creation_time': 30.0,  # seconds for 1000 users
        'query_time': 5.0,           # seconds for complex queries
        'bulk_update_time': 2.0,     # seconds for 1000 user updates
        'authentication_time': 5.0    # seconds for 100 authentications
    }
    
    # Test database settings
    TEST_DATABASE_SETTINGS = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'OPTIONS': {
            'timeout': 20,
        }
    }


def create_test_users_batch(count=10, prefix='batch'):
    """Utility function to create a batch of test users."""
    users = []
    for i in range(count):
        user_data = {
            'email': f'{prefix}{i}@example.com',
            'username': f'{prefix}_user_{i}',
            'password': f'{prefix}pass{i}'
        }
        users.append(User.objects.create_user(**user_data))
    return users


def cleanup_test_users(email_pattern=None, username_pattern=None):
    """Utility function to clean up test users."""
    queryset = User.objects.all()
    
    if email_pattern:
        queryset = queryset.filter(email__contains=email_pattern)
    
    if username_pattern:
        queryset = queryset.filter(username__contains=username_pattern)
    
    count = queryset.count()
    queryset.delete()
    return count