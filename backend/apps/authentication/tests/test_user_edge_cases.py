"""
Edge case and performance tests for User model.
"""
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.test.utils import override_settings
import time
from datetime import datetime, timedelta

User = get_user_model()


class UserEdgeCasesTest(TestCase):
    """Test edge cases for User model."""

    def test_user_with_very_long_email(self):
        """Test user creation with maximum length email."""
        # Django EmailField default max_length is 254
        long_email = 'a' * 240 + '@example.com'  # 252 characters
        
        user = User.objects.create_user(
            email=long_email,
            username='long_email_user',
            password='pass123'
        )
        
        self.assertEqual(user.email, long_email)

    def test_user_with_email_at_max_length_limit(self):
        """Test user creation with email at Django's max length limit."""
        # Test exactly at the 254 character limit
        max_email = 'a' * 242 + '@example.com'  # Exactly 254 characters
        
        user = User.objects.create_user(
            email=max_email,
            username='max_email_user',
            password='pass123'
        )
        
        self.assertEqual(user.email, max_email)

    def test_user_with_email_exceeding_max_length(self):
        """Test that email exceeding max length raises validation error."""
        # Test over the 254 character limit
        too_long_email = 'a' * 250 + '@example.com'  # 262 characters
        
        user = User(
            email=too_long_email,
            username='too_long_email_user',
            password='pass123'
        )
        
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_user_with_unicode_email(self):
        """Test user creation with unicode characters in email."""
        unicode_email = 'tëst@éxample.com'
        
        user = User.objects.create_user(
            email=unicode_email,
            username='unicode_user',
            password='pass123'
        )
        
        self.assertEqual(user.email, unicode_email)

    def test_user_with_special_characters_in_username(self):
        """Test user creation with special characters in username."""
        special_username = 'user-name_123.test'
        
        user = User.objects.create_user(
            email='special@example.com',
            username=special_username,
            password='pass123'
        )
        
        self.assertEqual(user.username, special_username)

    def test_user_creation_with_none_values(self):
        """Test user creation behavior with None values."""
        with self.assertRaises((IntegrityError, ValidationError)):
            User.objects.create_user(
                email=None,
                username='none_email_user',
                password='pass123'
            )

    def test_user_creation_with_empty_string_email(self):
        """Test user creation with empty string email."""
        user = User(
            email='',
            username='empty_email_user',
            password='pass123'
        )
        
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_user_creation_with_whitespace_email(self):
        """Test user creation with whitespace-only email."""
        user = User(
            email='   ',
            username='whitespace_user',
            password='pass123'
        )
        
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_user_timezone_handling(self):
        """Test that user timestamps handle timezone correctly."""
        with override_settings(USE_TZ=True):
            user = User.objects.create_user(
                email='timezone@example.com',
                username='timezone_user',
                password='pass123'
            )
            
            # Timestamps should be timezone-aware
            self.assertIsNotNone(user.created_at.tzinfo)
            self.assertIsNotNone(user.updated_at.tzinfo)

    def test_user_bulk_creation(self):
        """Test bulk creation of users."""
        users_data = [
            User(
                email=f'bulk{i}@example.com',
                username=f'bulk_user_{i}',
                password='pass123'
            )
            for i in range(100)
        ]
        
        # Bulk create should work
        created_users = User.objects.bulk_create(users_data)
        self.assertEqual(len(created_users), 100)
        
        # Verify they exist in database
        self.assertEqual(User.objects.filter(email__startswith='bulk').count(), 100)

    def test_user_with_duplicate_username_different_email(self):
        """Test creating users with same username but different emails."""
        # Create first user
        User.objects.create_user(
            email='first@example.com',
            username='duplicate_username',
            password='pass123'
        )
        
        # Create second user with same username but different email
        # This should work since email is the USERNAME_FIELD
        user2 = User.objects.create_user(
            email='second@example.com',
            username='duplicate_username',
            password='pass123'
        )
        
        self.assertEqual(user2.username, 'duplicate_username')
        self.assertEqual(user2.email, 'second@example.com')

    def test_user_case_sensitivity_in_email(self):
        """Test email case sensitivity behavior."""
        # Create user with lowercase email
        user1 = User.objects.create_user(
            email='case@example.com',
            username='case_user1',
            password='pass123'
        )
        
        # Create user with uppercase email (should work as Django doesn't enforce case-insensitive uniqueness)
        user2 = User.objects.create_user(
            email='CASE@EXAMPLE.COM',
            username='case_user2',
            password='pass123'
        )
        
        self.assertNotEqual(user1.email, user2.email)

    def test_user_password_hashing(self):
        """Test that passwords are properly hashed."""
        password = 'plaintext_password'
        user = User.objects.create_user(
            email='hash@example.com',
            username='hash_user',
            password=password
        )
        
        # Password should be hashed, not stored as plaintext
        self.assertNotEqual(user.password, password)
        self.assertTrue(user.password.startswith('pbkdf2_sha256$'))
        self.assertTrue(user.check_password(password))

    def test_user_last_login_update(self):
        """Test that last_login is updated on authentication."""
        user = User.objects.create_user(
            email='login@example.com',
            username='login_user',
            password='pass123'
        )
        
        # Initially last_login should be None
        self.assertIsNone(user.last_login)
        
        # Simulate login
        from django.contrib.auth import authenticate
        authenticated_user = authenticate(
            username='login@example.com',
            password='pass123'
        )
        
        # Update last_login manually (normally done by Django's login view)
        authenticated_user.last_login = timezone.now()
        authenticated_user.save()
        
        # Refresh from database
        user.refresh_from_db()
        self.assertIsNotNone(user.last_login)


class UserPerformanceTest(TestCase):
    """Performance tests for User model operations."""

    def test_user_creation_performance(self):
        """Test performance of user creation."""
        start_time = time.time()
        
        # Create 1000 users
        for i in range(1000):
            User.objects.create_user(
                email=f'perf{i}@example.com',
                username=f'perf_user_{i}',
                password='pass123'
            )
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # Should create 1000 users in reasonable time (adjust threshold as needed)
        self.assertLess(creation_time, 30.0, "User creation took too long")

    def test_user_query_performance(self):
        """Test performance of user queries."""
        # Create test users
        users = [
            User(
                email=f'query{i}@example.com',
                username=f'query_user_{i}',
                password='pass123'
            )
            for i in range(1000)
        ]
        User.objects.bulk_create(users)
        
        start_time = time.time()
        
        # Perform various queries
        User.objects.filter(email__contains='query').count()
        User.objects.filter(username__startswith='query_user').exists()
        list(User.objects.filter(is_active=True)[:100])
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Queries should complete in reasonable time
        self.assertLess(query_time, 5.0, "User queries took too long")

    def test_user_bulk_update_performance(self):
        """Test performance of bulk user updates."""
        # Create test users
        users = [
            User(
                email=f'update{i}@example.com',
                username=f'update_user_{i}',
                password='pass123'
            )
            for i in range(1000)
        ]
        User.objects.bulk_create(users)
        
        start_time = time.time()
        
        # Bulk update
        User.objects.filter(email__contains='update').update(
            first_name='Updated'
        )
        
        end_time = time.time()
        update_time = end_time - start_time
        
        # Bulk update should be fast
        self.assertLess(update_time, 2.0, "Bulk update took too long")

    def test_user_authentication_performance(self):
        """Test performance of user authentication."""
        # Create test user
        user = User.objects.create_user(
            email='auth_perf@example.com',
            username='auth_perf_user',
            password='pass123'
        )
        
        from django.contrib.auth import authenticate
        
        start_time = time.time()
        
        # Perform multiple authentications
        for _ in range(100):
            authenticate(
                username='auth_perf@example.com',
                password='pass123'
            )
        
        end_time = time.time()
        auth_time = end_time - start_time
        
        # Authentication should be reasonably fast
        self.assertLess(auth_time, 5.0, "Authentication took too long")


class UserConcurrencyTest(TestCase):
    """Test User model under concurrent access scenarios."""

    def test_concurrent_user_updates(self):
        """Test concurrent updates to the same user."""
        user = User.objects.create_user(
            email='concurrent@example.com',
            username='concurrent_user',
            password='pass123'
        )
        
        # Simulate concurrent updates
        user1 = User.objects.get(id=user.id)
        user2 = User.objects.get(id=user.id)
        
        user1.first_name = 'First'
        user2.last_name = 'Last'
        
        user1.save()
        user2.save()
        
        # Refresh and check final state
        user.refresh_from_db()
        self.assertEqual(user.last_name, 'Last')

    def test_user_creation_race_condition(self):
        """Test user creation under race conditions."""
        from threading import Thread, Barrier
        import threading
        
        results = []
        barrier = Barrier(2)
        
        def create_user_with_same_email():
            barrier.wait()  # Synchronize thread start
            try:
                user = User.objects.create_user(
                    email='race@example.com',
                    username=f'race_user_{threading.current_thread().ident}',
                    password='pass123'
                )
                results.append(('success', user.id))
            except IntegrityError as e:
                results.append(('error', str(e)))
        
        # Start two threads trying to create users with same email
        thread1 = Thread(target=create_user_with_same_email)
        thread2 = Thread(target=create_user_with_same_email)
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # One should succeed, one should fail due to unique constraint
        success_count = sum(1 for result in results if result[0] == 'success')
        error_count = sum(1 for result in results if result[0] == 'error')
        
        self.assertEqual(success_count, 1)
        self.assertEqual(error_count, 1)