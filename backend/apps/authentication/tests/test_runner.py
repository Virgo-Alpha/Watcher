"""
Custom test runner and test discovery for authentication app tests.
"""
import unittest
from django.test.runner import DiscoverRunner
from django.test import TestCase
from django.core.management import call_command
from django.db import connection
from django.conf import settings


class AuthenticationTestRunner(DiscoverRunner):
    """Custom test runner for authentication app with enhanced setup."""
    
    def setup_test_environment(self, **kwargs):
        """Set up test environment with authentication-specific settings."""
        super().setup_test_environment(**kwargs)
        
        # Ensure we're using the test database
        settings.DATABASES['default']['NAME'] = ':memory:'
        
        # Set up authentication-specific test settings
        settings.AUTH_USER_MODEL = 'authentication.User'
        settings.USE_TZ = True
        
    def setup_databases(self, **kwargs):
        """Set up test databases with proper migrations."""
        old_config = super().setup_databases(**kwargs)
        
        # Run authentication app migrations
        call_command('migrate', 'authentication', verbosity=0, interactive=False)
        
        return old_config
    
    def teardown_databases(self, old_config, **kwargs):
        """Clean up test databases."""
        super().teardown_databases(old_config, **kwargs)


class AuthenticationTestSuite:
    """Test suite organizer for authentication app tests."""
    
    @staticmethod
    def get_test_modules():
        """Get list of test modules in authentication app."""
        return [
            'apps.authentication.tests.test_models',
            'apps.authentication.tests.test_user_integration',
            'apps.authentication.tests.test_user_edge_cases',
        ]
    
    @staticmethod
    def create_test_suite():
        """Create a comprehensive test suite for authentication app."""
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add all test modules
        for module_name in AuthenticationTestSuite.get_test_modules():
            try:
                module_suite = loader.loadTestsFromName(module_name)
                suite.addTest(module_suite)
            except ImportError as e:
                print(f"Warning: Could not import test module {module_name}: {e}")
        
        return suite
    
    @staticmethod
    def run_tests():
        """Run all authentication tests."""
        suite = AuthenticationTestSuite.create_test_suite()
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return result.wasSuccessful()


class AuthenticationTestMixin:
    """Mixin class providing common test utilities for authentication tests."""
    
    def setUp(self):
        """Set up common test data."""
        super().setUp()
        self.test_user_data = {
            'email': 'mixin@example.com',
            'username': 'mixin_user',
            'password': 'mixinpass123'
        }
    
    def create_authenticated_user(self):
        """Create and return an authenticated user for tests."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user = User.objects.create_user(**self.test_user_data)
        
        # Simulate authentication
        from django.contrib.auth import authenticate
        authenticated_user = authenticate(
            username=self.test_user_data['email'],
            password=self.test_user_data['password']
        )
        
        return authenticated_user
    
    def assert_user_authenticated(self, user):
        """Assert that a user is properly authenticated."""
        self.assertIsNotNone(user)
        self.assertTrue(user.is_authenticated)
        self.assertIsNotNone(user.email)
    
    def assert_user_permissions(self, user, permissions):
        """Assert that a user has specific permissions."""
        for permission in permissions:
            self.assertTrue(
                user.has_perm(permission),
                f"User does not have permission: {permission}"
            )


# Test discovery functions
def discover_authentication_tests():
    """Discover all tests in the authentication app."""
    loader = unittest.TestLoader()
    start_dir = 'apps/authentication/tests'
    suite = loader.discover(start_dir, pattern='test_*.py')
    return suite


def run_authentication_tests():
    """Run all authentication tests with detailed output."""
    suite = discover_authentication_tests()
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=None,
        descriptions=True,
        failfast=False
    )
    result = runner.run(suite)
    
    # Print summary
    print(f"\nTest Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    # Run tests when script is executed directly
    success = run_authentication_tests()
    exit(0 if success else 1)