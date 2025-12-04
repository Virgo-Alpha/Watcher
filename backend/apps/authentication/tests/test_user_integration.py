"""
Integration tests for User model with other Django components.
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.test.client import Client
from django.urls import reverse
from django.core.management import call_command
from django.db.migrations.executor import MigrationExecutor
from django.db import connection

User = get_user_model()


class UserAuthenticationIntegrationTest(TestCase):
    """Test User model integration with Django's authentication system."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user_data = {
            'email': 'integration@example.com',
            'username': 'integration_user',
            'password': 'integrationpass123'
        }

    def test_user_login_with_email(self):
        """Test that user can log in using email."""
        user = User.objects.create_user(**self.user_data)
        
        # Test authentication with email
        authenticated_user = authenticate(
            username=self.user_data['email'],
            password=self.user_data['password']
        )
        
        self.assertEqual(authenticated_user, user)
        self.assertTrue(authenticated_user.is_authenticated)

    def test_user_session_management(self):
        """Test user session creation and management."""
        user = User.objects.create_user(**self.user_data)
        
        # Test login creates session
        login_successful = self.client.login(
            username=self.user_data['email'],
            password=self.user_data['password']
        )
        
        self.assertTrue(login_successful)
        self.assertIn('_auth_user_id', self.client.session)

    def test_user_permissions_integration(self):
        """Test User model integration with Django permissions."""
        user = User.objects.create_user(**self.user_data)
        
        # Get a permission
        content_type = ContentType.objects.get_for_model(User)
        permission = Permission.objects.create(
            codename='test_permission',
            name='Test Permission',
            content_type=content_type
        )
        
        # Assign permission to user
        user.user_permissions.add(permission)
        
        # Test permission checking
        self.assertTrue(user.has_perm('authentication.test_permission'))

    def test_user_groups_integration(self):
        """Test User model integration with Django groups."""
        user = User.objects.create_user(**self.user_data)
        
        # Create group with permission
        group = Group.objects.create(name='test_group')
        content_type = ContentType.objects.get_for_model(User)
        permission = Permission.objects.create(
            codename='group_permission',
            name='Group Permission',
            content_type=content_type
        )
        group.permissions.add(permission)
        
        # Add user to group
        user.groups.add(group)
        
        # Test permission through group
        self.assertTrue(user.has_perm('authentication.group_permission'))


class UserDatabaseIntegrationTest(TransactionTestCase):
    """Test User model database-level integration."""

    def test_user_creation_in_transaction(self):
        """Test user creation within database transaction."""
        with transaction.atomic():
            user = User.objects.create_user(
                email='transaction@example.com',
                username='transaction_user',
                password='transactionpass123'
            )
            
            # User should exist within transaction
            self.assertTrue(User.objects.filter(email=user.email).exists())

    def test_user_rollback_on_error(self):
        """Test that user creation is rolled back on error."""
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    email='rollback@example.com',
                    username='rollback_user',
                    password='rollbackpass123'
                )
                
                # Force an error
                raise Exception("Forced error for rollback test")
                
        except Exception:
            pass
        
        # User should not exist after rollback
        self.assertFalse(User.objects.filter(email='rollback@example.com').exists())

    def test_concurrent_user_creation(self):
        """Test concurrent user creation scenarios."""
        from threading import Thread
        import time
        
        results = []
        
        def create_user(email_suffix):
            try:
                user = User.objects.create_user(
                    email=f'concurrent{email_suffix}@example.com',
                    username=f'concurrent_user_{email_suffix}',
                    password='concurrentpass123'
                )
                results.append(user.id)
            except Exception as e:
                results.append(str(e))
        
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = Thread(target=create_user, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All users should be created successfully
        self.assertEqual(len(results), 3)
        self.assertTrue(all(isinstance(result, int) for result in results))


class UserMigrationTest(TransactionTestCase):
    """Test User model migrations."""

    def test_user_model_migration_state(self):
        """Test that User model migrations are properly applied."""
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        
        # Should have no pending migrations
        self.assertEqual(len(plan), 0, "There are pending migrations")

    def test_user_table_structure(self):
        """Test that User table has expected structure."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'auth_user'
                ORDER BY column_name
            """)
            columns = cursor.fetchall()
        
        # Convert to dict for easier testing
        column_info = {col[0]: {'type': col[1], 'nullable': col[2]} for col in columns}
        
        # Test key columns exist
        expected_columns = ['email', 'created_at', 'updated_at', 'username', 'password']
        for col in expected_columns:
            self.assertIn(col, column_info, f"Column {col} not found in User table")


class UserAdminIntegrationTest(TestCase):
    """Test User model integration with Django admin."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='adminpass123'
        )
        self.client = Client()

    def test_user_admin_registration(self):
        """Test that User model is properly registered with admin."""
        from django.contrib import admin
        from apps.authentication.models import User
        
        # User should be registered in admin
        self.assertIn(User, admin.site._registry)

    def test_user_admin_access(self):
        """Test admin access to User model."""
        self.client.force_login(self.admin_user)
        
        # Should be able to access user changelist
        response = self.client.get('/admin/authentication/user/')
        self.assertEqual(response.status_code, 200)


class UserSignalIntegrationTest(TestCase):
    """Test User model integration with Django signals."""

    def test_user_post_save_signal(self):
        """Test that post_save signal is fired for User creation."""
        from django.db.models.signals import post_save
        
        signal_fired = []
        
        def signal_handler(sender, instance, created, **kwargs):
            if created:
                signal_fired.append(instance.id)
        
        # Connect signal
        post_save.connect(signal_handler, sender=User)
        
        try:
            # Create user
            user = User.objects.create_user(
                email='signal@example.com',
                username='signal_user',
                password='signalpass123'
            )
            
            # Signal should have fired
            self.assertIn(user.id, signal_fired)
            
        finally:
            # Disconnect signal
            post_save.disconnect(signal_handler, sender=User)

    def test_user_pre_delete_signal(self):
        """Test that pre_delete signal is fired for User deletion."""
        from django.db.models.signals import pre_delete
        
        signal_fired = []
        
        def signal_handler(sender, instance, **kwargs):
            signal_fired.append(instance.id)
        
        # Connect signal
        pre_delete.connect(signal_handler, sender=User)
        
        try:
            # Create and delete user
            user = User.objects.create_user(
                email='delete@example.com',
                username='delete_user',
                password='deletepass123'
            )
            user_id = user.id
            user.delete()
            
            # Signal should have fired
            self.assertIn(user_id, signal_fired)
            
        finally:
            # Disconnect signal
            pre_delete.disconnect(signal_handler, sender=User)