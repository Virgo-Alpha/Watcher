"""
Tests for haunt serializers.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from ..models import Folder, Haunt
from ..serializers import HauntSerializer, HauntListSerializer

User = get_user_model()


class HauntSerializerTestCase(TestCase):
    """Test case for HauntSerializer"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.folder = Folder.objects.create(
            user=self.user,
            name='Test Folder'
        )
        self.haunt = Haunt.objects.create(
            owner=self.user,
            name='Test Haunt',
            url='https://example.com',
            description='Test description',
            folder=self.folder,
            config={
                'selectors': {'status': 'css:.status'},
                'normalization': {'status': {'type': 'text'}},
                'truthy_values': {'status': ['open']}
            }
        )

    def get_serializer_context(self):
        """Create serializer context with request"""
        request = self.factory.get('/')
        request.user = self.user
        return {'request': request}

    def test_haunt_serializer_includes_all_fields(self):
        """Test that HauntSerializer includes all expected fields"""
        context = self.get_serializer_context()
        serializer = HauntSerializer(self.haunt, context=context)
        data = serializer.data

        expected_fields = [
            'id', 'name', 'url', 'description', 'config', 'current_state',
            'last_alert_state', 'alert_mode', 'alert_mode_display',
            'scrape_interval', 'scrape_interval_display', 'is_public',
            'public_slug', 'is_active', 'last_scraped_at', 'last_error',
            'error_count', 'is_healthy', 'folder', 'folder_name',
            'unread_count', 'public_url', 'rss_url', 'created_at', 'updated_at'
        ]

        for field in expected_fields:
            self.assertIn(field, data, f"Field '{field}' missing from serializer")

    def test_haunt_serializer_folder_name(self):
        """Test that folder_name is correctly populated"""
        context = self.get_serializer_context()
        serializer = HauntSerializer(self.haunt, context=context)
        self.assertEqual(serializer.data['folder_name'], 'Test Folder')

    def test_haunt_serializer_folder_name_none(self):
        """Test that folder_name is None when haunt has no folder"""
        haunt_no_folder = Haunt.objects.create(
            owner=self.user,
            name='No Folder Haunt',
            url='https://example.com/nofolder'
        )
        context = self.get_serializer_context()
        serializer = HauntSerializer(haunt_no_folder, context=context)
        self.assertIsNone(serializer.data['folder_name'])

    def test_haunt_serializer_display_fields(self):
        """Test that display fields are included"""
        context = self.get_serializer_context()
        serializer = HauntSerializer(self.haunt, context=context)
        data = serializer.data

        self.assertIn('scrape_interval_display', data)
        self.assertIn('alert_mode_display', data)
        self.assertIsNotNone(data['scrape_interval_display'])
        self.assertIsNotNone(data['alert_mode_display'])

    def test_haunt_serializer_urls(self):
        """Test that public_url and rss_url are generated"""
        context = self.get_serializer_context()
        serializer = HauntSerializer(self.haunt, context=context)
        data = serializer.data

        self.assertIn('public_url', data)
        self.assertIn('rss_url', data)

    def test_haunt_serializer_validate_folder_same_user(self):
        """Test that folder validation requires same user"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_folder = Folder.objects.create(
            user=other_user,
            name='Other Folder'
        )

        context = self.get_serializer_context()
        serializer = HauntSerializer(data={
            'name': 'Invalid Folder Haunt',
            'url': 'https://example.com/invalid',
            'folder': other_folder.id,
            'config': {
                'selectors': {},
                'normalization': {},
                'truthy_values': {}
            }
        }, context=context)

        self.assertFalse(serializer.is_valid())
        self.assertIn('folder', serializer.errors)

    def test_haunt_serializer_validate_config_structure(self):
        """Test that config validation requires all keys"""
        context = self.get_serializer_context()

        # Missing normalization key
        serializer = HauntSerializer(data={
            'name': 'Invalid Config',
            'url': 'https://example.com/invalid',
            'config': {
                'selectors': {},
                'truthy_values': {}
            }
        }, context=context)

        self.assertFalse(serializer.is_valid())
        self.assertIn('config', serializer.errors)

    def test_haunt_serializer_validate_scrape_interval(self):
        """Test that scrape interval validation works"""
        context = self.get_serializer_context()

        serializer = HauntSerializer(data={
            'name': 'Invalid Interval',
            'url': 'https://example.com/invalid',
            'scrape_interval': 999,  # Invalid interval
            'config': {
                'selectors': {},
                'normalization': {},
                'truthy_values': {}
            }
        }, context=context)

        self.assertFalse(serializer.is_valid())
        self.assertIn('scrape_interval', serializer.errors)

    def test_haunt_serializer_validate_alert_mode(self):
        """Test that alert mode validation works"""
        context = self.get_serializer_context()

        serializer = HauntSerializer(data={
            'name': 'Invalid Alert Mode',
            'url': 'https://example.com/invalid',
            'alert_mode': 'invalid_mode',
            'config': {
                'selectors': {},
                'normalization': {},
                'truthy_values': {}
            }
        }, context=context)

        self.assertFalse(serializer.is_valid())
        self.assertIn('alert_mode', serializer.errors)

    def test_haunt_serializer_create_sets_owner(self):
        """Test that create method sets owner from request"""
        context = self.get_serializer_context()

        serializer = HauntSerializer(data={
            'name': 'New Haunt',
            'url': 'https://example.com/new',
            'config': {
                'selectors': {},
                'normalization': {},
                'truthy_values': {}
            }
        }, context=context)

        self.assertTrue(serializer.is_valid())
        haunt = serializer.save()

        self.assertEqual(haunt.owner, self.user)

    def test_haunt_serializer_empty_config_allowed(self):
        """Test that empty config dict is allowed"""
        context = self.get_serializer_context()

        serializer = HauntSerializer(data={
            'name': 'Empty Config',
            'url': 'https://example.com/empty',
            'config': {}
        }, context=context)

        self.assertTrue(serializer.is_valid())


class HauntListSerializerTestCase(TestCase):
    """Test case for HauntListSerializer"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.folder = Folder.objects.create(
            user=self.user,
            name='Test Folder'
        )
        self.haunt = Haunt.objects.create(
            owner=self.user,
            name='Test Haunt',
            url='https://example.com',
            folder=self.folder
        )

    def get_serializer_context(self):
        """Create serializer context with request"""
        request = self.factory.get('/')
        request.user = self.user
        return {'request': request}

    def test_haunt_list_serializer_includes_essential_fields(self):
        """Test that HauntListSerializer includes essential fields only"""
        context = self.get_serializer_context()
        serializer = HauntListSerializer(self.haunt, context=context)
        data = serializer.data

        expected_fields = [
            'id', 'name', 'url', 'is_public', 'is_active', 'folder',
            'folder_name', 'unread_count', 'scrape_interval',
            'scrape_interval_display', 'last_scraped_at', 'is_healthy',
            'created_at'
        ]

        for field in expected_fields:
            self.assertIn(field, data, f"Field '{field}' missing from list serializer")

    def test_haunt_list_serializer_excludes_heavy_fields(self):
        """Test that HauntListSerializer excludes heavy fields"""
        context = self.get_serializer_context()
        serializer = HauntListSerializer(self.haunt, context=context)
        data = serializer.data

        # These fields should not be in list serializer
        excluded_fields = [
            'config', 'current_state', 'last_alert_state', 'description',
            'last_error', 'public_url', 'rss_url'
        ]

        for field in excluded_fields:
            self.assertNotIn(field, data, f"Field '{field}' should not be in list serializer")

    def test_haunt_list_serializer_folder_name(self):
        """Test that folder_name is correctly populated in list serializer"""
        context = self.get_serializer_context()
        serializer = HauntListSerializer(self.haunt, context=context)
        self.assertEqual(serializer.data['folder_name'], 'Test Folder')

    def test_haunt_list_serializer_multiple_haunts(self):
        """Test serializing multiple haunts"""
        haunt2 = Haunt.objects.create(
            owner=self.user,
            name='Second Haunt',
            url='https://example.com/2'
        )

        context = self.get_serializer_context()
        haunts = [self.haunt, haunt2]
        serializer = HauntListSerializer(haunts, many=True, context=context)

        self.assertEqual(len(serializer.data), 2)
        self.assertEqual(serializer.data[0]['name'], 'Test Haunt')
        self.assertEqual(serializer.data[1]['name'], 'Second Haunt')

    def test_haunt_list_serializer_performance_fields(self):
        """Test that performance-related fields are included"""
        context = self.get_serializer_context()
        serializer = HauntListSerializer(self.haunt, context=context)
        data = serializer.data

        # These fields are important for UI performance
        self.assertIn('is_healthy', data)
        self.assertIn('scrape_interval_display', data)
        self.assertIn('unread_count', data)
