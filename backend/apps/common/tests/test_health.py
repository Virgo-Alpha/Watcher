"""
Tests for health check functionality
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class HealthCheckTestCase(TestCase):
    """Test health check endpoints"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_basic_health_check(self):
        """Test basic health check endpoint"""
        response = self.client.get(reverse('health-check'))
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE])
        self.assertIn('status', response.data)
        self.assertIn('checks', response.data)
        self.assertIn('database', response.data['checks'])
        self.assertIn('cache', response.data['checks'])
    
    def test_detailed_health_check(self):
        """Test detailed health check endpoint"""
        response = self.client.get(reverse('health-check-detailed'))
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE])
        self.assertIn('status', response.data)
        self.assertIn('checks', response.data)
        
        # Check all components are present
        expected_checks = ['database', 'cache', 'celery', 'ai_service', 'browser_pool']
        for check in expected_checks:
            self.assertIn(check, response.data['checks'])
    
    def test_readiness_check(self):
        """Test readiness check endpoint"""
        response = self.client.get(reverse('readiness-check'))
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE])
        self.assertIn('status', response.data)
    
    def test_liveness_check(self):
        """Test liveness check endpoint"""
        response = self.client.get(reverse('liveness-check'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'alive')
