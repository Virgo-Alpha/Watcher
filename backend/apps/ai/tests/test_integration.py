"""
Integration tests for AI service API endpoints
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class AIConfigPreviewIntegrationTest(TestCase):
    """Integration tests for the generate-config-preview endpoint"""
    
    def setUp(self):
        """Set up test client and user"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_generate_config_preview_success(self):
        """Test successful config preview generation"""
        response = self.client.post(
            '/api/v1/haunts/generate-config-preview/',
            {
                'url': 'https://example.com/jobs',
                'description': 'Check if applications are open'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('config', response.data)
        self.assertIn('success', response.data)
        self.assertTrue(response.data['success'])
        
        # Check config structure
        config = response.data['config']
        self.assertIn('selectors', config)
        self.assertIn('normalization', config)
        self.assertIn('truthy_values', config)
    
    def test_generate_config_preview_missing_url(self):
        """Test that missing URL returns 400"""
        response = self.client.post(
            '/api/v1/haunts/generate-config-preview/',
            {
                'description': 'Check if applications are open'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_generate_config_preview_missing_description(self):
        """Test that missing description returns 400"""
        response = self.client.post(
            '/api/v1/haunts/generate-config-preview/',
            {
                'url': 'https://example.com/jobs'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_generate_config_preview_unauthorized(self):
        """Test that unauthorized request returns 401"""
        # Remove credentials
        self.client.credentials()
        
        response = self.client.post(
            '/api/v1/haunts/generate-config-preview/',
            {
                'url': 'https://example.com/jobs',
                'description': 'Check if applications are open'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, 401)
