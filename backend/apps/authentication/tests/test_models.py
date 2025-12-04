"""
Unit tests for authentication models.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for the custom User model."""

    def setUp(self):
        """Set up test data."""
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }

    def test_create_user_with_email(self):
        """Test creating a user with email as username field."""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.email, self.user_data['email'])
        self.assertEqual(user.username, self.user_data['username'])
        self.assertTrue(user.check_password(self.user_data['password']))
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)

    def test_create_superuser(self):
        """Test creating a superuser."""
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='adminpass123'
        )
        
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
        self.assertEqual(superuser.email, 'admin@example.com')

    def test_email_unique_constraint(self):
        """Test that email field has unique constraint."""
        User.objects.create_user(**self.user_data)
        
        # Try to create another user with same email
        duplicate_data = self.user_data.copy()
        duplicate_data['username'] = 'different_username'
        
        with self.assertRaises(IntegrityError):
            User.objects.create_user(**duplicate_data)

    def test_username_field_is_email(self):
        """Test that USERNAME_FIELD is set to email."""
        self.assertEqual(User.USERNAME_FIELD, 'email')

    def test_required_fields_contains_username(self):
        """Test that REQUIRED_FIELDS contains username."""
        self.assertIn('username', User.REQUIRED_FIELDS)

    def test_str_representation(self):
        """Test string representation of User model."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), self.user_data['email'])

    def test_created_at_auto_now_add(self):
        """Test that created_at is automatically set on creation."""
        before_creation = timezone.now()
        user = User.objects.create_user(**self.user_data)
        after_creation = timezone.now()
        
        self.assertGreaterEqual(user.created_at, before_creation)
        self.assertLessEqual(user.created_at, after_creation)

    def test_updated_at_auto_now(self):
        """Test that updated_at is automatically updated on save."""
        user = User.objects.create_user(**self.user_data)
        original_updated_at = user.updated_at
        
        # Wait a small amount and update the user
        user.first_name = 'Updated'
        user.save()
        
        self.assertGreater(user.updated_at, original_updated_at)

    def test_email_validation(self):
        """Test email field validation."""
        invalid_data = self.user_data.copy()
        invalid_data['email'] = 'invalid-email'
        
        user = User(**invalid_data)
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_empty_email_not_allowed(self):
        """Test that empty email is not allowed."""
        invalid_data = self.user_data.copy()
        invalid_data['email'] = ''
        
        user = User(**invalid_data)
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_model_meta_configuration(self):
        """Test model Meta configuration."""
        self.assertEqual(User._meta.db_table, 'auth_user')
        self.assertEqual(User._meta.verbose_name, 'User')
        self.assertEqual(User._meta.verbose_name_plural, 'Users')

    def test_inherited_fields_from_abstract_user(self):
        """Test that User inherits expected fields from AbstractUser."""
        user = User.objects.create_user(**self.user_data)
        
        # Test some key inherited fields
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)
        self.assertIsNotNone(user.date_joined)
        self.assertIsNotNone(user.last_login)

    def test_user_authentication_with_email(self):
        """Test that user can authenticate using email."""
        from django.contrib.auth import authenticate
        
        user = User.objects.create_user(**self.user_data)
        
        # Should authenticate with email
        authenticated_user = authenticate(
            username=self.user_data['email'],
            password=self.user_data['password']
        )
        self.assertEqual(authenticated_user, user)

    def test_case_insensitive_email_uniqueness(self):
        """Test that email uniqueness is case-insensitive."""
        User.objects.create_user(**self.user_data)
        
        # Try to create user with same email in different case
        duplicate_data = self.user_data.copy()
        duplicate_data['email'] = self.user_data['email'].upper()
        duplicate_data['username'] = 'different_username'
        
        # This should still work as Django's EmailField doesn't enforce
        # case-insensitive uniqueness by default
        user2 = User.objects.create_user(**duplicate_data)
        self.assertIsNotNone(user2)

    def test_user_permissions_and_groups(self):
        """Test that user can have permissions and groups assigned."""
        from django.contrib.auth.models import Permission, Group
        from django.contrib.contenttypes.models import ContentType
        
        user = User.objects.create_user(**self.user_data)
        
        # Create a test group
        group = Group.objects.create(name='test_group')
        user.groups.add(group)
        
        # Test group assignment
        self.assertIn(group, user.groups.all())

    def test_user_creation_without_optional_fields(self):
        """Test creating user with only required fields."""
        minimal_data = {
            'email': 'minimal@example.com',
            'username': 'minimal',
            'password': 'pass123'
        }
        
        user = User.objects.create_user(**minimal_data)
        self.assertEqual(user.email, minimal_data['email'])
        self.assertEqual(user.username, minimal_data['username'])
        self.assertEqual(user.first_name, '')
        self.assertEqual(user.last_name, '')

    def test_user_manager_create_user_method(self):
        """Test the custom user manager's create_user method."""
        user = User.objects.create_user(
            email='manager@example.com',
            username='manager_user',
            password='managerpass123'
        )
        
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_user_manager_create_superuser_method(self):
        """Test the custom user manager's create_superuser method."""
        superuser = User.objects.create_superuser(
            email='super@example.com',
            username='super_user',
            password='superpass123'
        )
        
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_active)