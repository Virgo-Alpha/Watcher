"""
Integration tests for AI-powered haunt creation and preview functionality.
"""
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from ..models import Folder, Haunt
from apps.ai.services import AIConfigService, AIConfigurationError

User = get_user_model()


class AIHauntCreationTestCase(TestCase):
    """Test case for AI-powered haunt creation"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create test folder
        self.folder = Folder.objects.create(
            user=self.user,
            name='Test Folder'
        )

        # Sample AI-generated config
        self.sample_config = {
            'selectors': {
                'status': 'css:.admission-status',
                'deadline': 'css:.deadline-date'
            },
            'normalization': {
                'status': {
                    'type': 'text',
                    'transform': 'lowercase',
                    'strip': True
                },
                'deadline': {
                    'type': 'text',
                    'strip': True
                }
            },
            'truthy_values': {
                'status': ['open', 'accepting', 'available']
            }
        }

    def authenticate(self):
        """Authenticate test user"""
        self.client.force_authenticate(user=self.user)

    @patch.object(AIConfigService, 'is_available', return_value=True)
    @patch.object(AIConfigService, 'generate_config')
    def test_create_haunt_with_ai_success(self, mock_generate_config, mock_is_available):
        """Test successful haunt creation with AI"""
        self.authenticate()

        # Mock AI service response
        mock_generate_config.return_value = self.sample_config

        url = reverse('haunt-create-with-ai')
        data = {
            'url': 'https://example.com/admissions',
            'description': 'Monitor the admission status and deadline',
            'name': 'University Admissions',
            'scrape_interval': 60,
            'alert_mode': 'on_change'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'University Admissions')
        self.assertEqual(response.data['url'], 'https://example.com/admissions')
        self.assertEqual(response.data['description'], 'Monitor the admission status and deadline')
        self.assertIn('config', response.data)
        self.assertEqual(response.data['config'], self.sample_config)

        # Verify haunt was created in database
        haunt = Haunt.objects.get(id=response.data['id'])
        self.assertEqual(haunt.owner, self.user)
        self.assertEqual(haunt.config, self.sample_config)

        # Verify AI service was called correctly
        mock_generate_config.assert_called_once_with(
            'https://example.com/admissions',
            'Monitor the admission status and deadline'
        )

    @patch.object(AIConfigService, 'is_available', return_value=True)
    @patch.object(AIConfigService, 'generate_config')
    def test_create_haunt_with_ai_auto_name(self, mock_generate_config, mock_is_available):
        """Test haunt creation with auto-generated name"""
        self.authenticate()

        mock_generate_config.return_value = self.sample_config

        url = reverse('haunt-create-with-ai')
        data = {
            'url': 'https://example.com/status',
            'description': 'Monitor status changes'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Name should be auto-generated from URL
        self.assertEqual(response.data['name'], 'example.com')

    @patch.object(AIConfigService, 'is_available', return_value=True)
    @patch.object(AIConfigService, 'generate_config')
    def test_create_haunt_with_ai_and_folder(self, mock_generate_config, mock_is_available):
        """Test haunt creation with folder assignment"""
        self.authenticate()

        mock_generate_config.return_value = self.sample_config

        url = reverse('haunt-create-with-ai')
        data = {
            'url': 'https://example.com/jobs',
            'description': 'Monitor job postings',
            'name': 'Job Board',
            'folder': self.folder.id
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['folder'], self.folder.id)

        # Verify in database
        haunt = Haunt.objects.get(id=response.data['id'])
        self.assertEqual(haunt.folder, self.folder)

    @patch.object(AIConfigService, 'is_available')
    def test_create_haunt_with_ai_service_unavailable(self, mock_is_available):
        """Test haunt creation when AI service is unavailable"""
        self.authenticate()

        # Mock AI service as unavailable
        mock_is_available.return_value = False

        url = reverse('haunt-create-with-ai')
        data = {
            'url': 'https://example.com',
            'description': 'Test description'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('error', response.data)
        self.assertIn('AI service is not available', response.data['error'])
        self.assertIn('fallback', response.data)

    @patch.object(AIConfigService, 'is_available', return_value=True)
    @patch.object(AIConfigService, 'generate_config')
    def test_create_haunt_with_ai_generation_error(self, mock_generate_config, mock_is_available):
        """Test haunt creation when AI generation fails"""
        self.authenticate()

        # Mock AI service to raise error
        mock_generate_config.side_effect = AIConfigurationError('Invalid response from LLM')

        url = reverse('haunt-create-with-ai')
        data = {
            'url': 'https://example.com',
            'description': 'Test description'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Invalid response from LLM', response.data['error'])
        self.assertIn('fallback', response.data)

    def test_create_haunt_with_ai_missing_url(self):
        """Test haunt creation with missing URL"""
        self.authenticate()

        url = reverse('haunt-create-with-ai')
        data = {
            'description': 'Test description'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('url', response.data)

    def test_create_haunt_with_ai_missing_description(self):
        """Test haunt creation with missing description"""
        self.authenticate()

        url = reverse('haunt-create-with-ai')
        data = {
            'url': 'https://example.com'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('description', response.data)

    def test_create_haunt_with_ai_invalid_folder(self):
        """Test haunt creation with folder from different user"""
        self.authenticate()

        # Create another user and their folder
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_folder = Folder.objects.create(
            user=other_user,
            name='Other Folder'
        )

        url = reverse('haunt-create-with-ai')
        data = {
            'url': 'https://example.com',
            'description': 'Test description',
            'folder': other_folder.id
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('folder', response.data)

    def test_create_haunt_with_ai_unauthenticated(self):
        """Test haunt creation without authentication"""
        url = reverse('haunt-create-with-ai')
        data = {
            'url': 'https://example.com',
            'description': 'Test description'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ConfigPreviewTestCase(TestCase):
    """Test case for configuration preview endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.sample_config = {
            'selectors': {
                'price': 'css:.price'
            },
            'normalization': {
                'price': {
                    'type': 'number'
                }
            },
            'truthy_values': {
                'price': []
            }
        }

    def authenticate(self):
        """Authenticate test user"""
        self.client.force_authenticate(user=self.user)

    @patch.object(AIConfigService, 'is_available', return_value=True)
    @patch.object(AIConfigService, 'generate_config')
    def test_generate_config_preview_success(self, mock_generate_config, mock_is_available):
        """Test successful config preview generation"""
        self.authenticate()

        mock_generate_config.return_value = self.sample_config

        url = reverse('haunt-generate-config-preview')
        data = {
            'url': 'https://example.com/product',
            'description': 'Monitor product price'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['url'], 'https://example.com/product')
        self.assertEqual(response.data['description'], 'Monitor product price')
        self.assertEqual(response.data['config'], self.sample_config)

        # Verify AI service was called
        mock_generate_config.assert_called_once_with(
            'https://example.com/product',
            'Monitor product price'
        )

    @patch.object(AIConfigService, 'is_available')
    def test_generate_config_preview_service_unavailable(self, mock_is_available):
        """Test config preview when AI service is unavailable"""
        self.authenticate()

        mock_is_available.return_value = False

        url = reverse('haunt-generate-config-preview')
        data = {
            'url': 'https://example.com',
            'description': 'Test description'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('error', response.data)

    def test_generate_config_preview_missing_url(self):
        """Test config preview with missing URL"""
        self.authenticate()

        url = reverse('haunt-generate-config-preview')
        data = {
            'description': 'Test description'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_generate_config_preview_missing_description(self):
        """Test config preview with missing description"""
        self.authenticate()

        url = reverse('haunt-generate-config-preview')
        data = {
            'url': 'https://example.com'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class TestScrapeTestCase(TestCase):
    """Test case for test scrape endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.sample_config = {
            'selectors': {
                'title': 'css:h1',
                'status': 'css:.status'
            },
            'normalization': {
                'title': {
                    'type': 'text',
                    'strip': True
                },
                'status': {
                    'type': 'text',
                    'transform': 'lowercase'
                }
            },
            'truthy_values': {
                'status': ['active', 'open']
            }
        }

    def authenticate(self):
        """Authenticate test user"""
        self.client.force_authenticate(user=self.user)

    @patch('apps.scraping.services.ScrapingService.scrape_url')
    def test_test_scrape_success(self, mock_scrape_url):
        """Test successful test scrape"""
        self.authenticate()

        # Mock scraping service response
        mock_scrape_url.return_value = {
            'title': 'Test Page',
            'status': 'active'
        }

        url = reverse('haunt-test-scrape')
        data = {
            'url': 'https://example.com',
            'config': self.sample_config
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['url'], 'https://example.com')
        self.assertIn('extracted_data', response.data)
        self.assertEqual(response.data['extracted_data']['title'], 'Test Page')
        self.assertEqual(response.data['extracted_data']['status'], 'active')

        # Verify scraping service was called
        mock_scrape_url.assert_called_once_with('https://example.com', self.sample_config)

    def test_test_scrape_missing_url(self):
        """Test test scrape with missing URL"""
        self.authenticate()

        url = reverse('haunt-test-scrape')
        data = {
            'config': self.sample_config
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_test_scrape_missing_config(self):
        """Test test scrape with missing config"""
        self.authenticate()

        url = reverse('haunt-test-scrape')
        data = {
            'url': 'https://example.com'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_test_scrape_invalid_config(self):
        """Test test scrape with invalid config structure"""
        self.authenticate()

        url = reverse('haunt-test-scrape')
        data = {
            'url': 'https://example.com',
            'config': {
                'selectors': {}  # Missing required keys
            }
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    @patch('apps.scraping.services.ScrapingService.scrape_url')
    def test_test_scrape_scraping_error(self, mock_scrape_url):
        """Test test scrape when scraping fails"""
        self.authenticate()

        # Mock scraping service to raise error
        from apps.scraping.services import ScrapingError
        mock_scrape_url.side_effect = ScrapingError('Page load timeout')

        url = reverse('haunt-test-scrape')
        data = {
            'url': 'https://example.com',
            'config': self.sample_config
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Page load timeout', response.data['error'])

    def test_test_scrape_unauthenticated(self):
        """Test test scrape without authentication"""
        url = reverse('haunt-test-scrape')
        data = {
            'url': 'https://example.com',
            'config': self.sample_config
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
