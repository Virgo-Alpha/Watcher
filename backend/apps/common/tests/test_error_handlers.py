"""
Tests for error handling functionality
"""
from django.test import TestCase
from rest_framework import status
from rest_framework.exceptions import ValidationError, NotFound

from apps.common.error_handlers import format_error_response, ErrorLogger
from apps.common.exceptions import (
    ServiceUnavailableError,
    RateLimitExceededError,
    ResourceNotFoundError
)


class ErrorHandlerTestCase(TestCase):
    """Test error handling utilities"""
    
    def test_format_error_response(self):
        """Test error response formatting"""
        response = format_error_response(
            error_code='test_error',
            message='Test error message',
            details={'field': 'value'},
            status_code=400
        )
        
        self.assertIn('error', response)
        self.assertEqual(response['error']['code'], 'test_error')
        self.assertEqual(response['error']['message'], 'Test error message')
        self.assertEqual(response['error']['status'], 400)
        self.assertEqual(response['error']['details'], {'field': 'value'})
    
    def test_format_error_response_without_details(self):
        """Test error response formatting without details"""
        response = format_error_response(
            error_code='test_error',
            message='Test error message',
            status_code=400
        )
        
        self.assertIn('error', response)
        self.assertNotIn('details', response['error'])
    
    def test_custom_exceptions(self):
        """Test custom exception classes"""
        # Test ServiceUnavailableError
        exc = ServiceUnavailableError("Service down")
        self.assertEqual(exc.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Test RateLimitExceededError
        exc = RateLimitExceededError("Too many requests")
        self.assertEqual(exc.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Test ResourceNotFoundError
        exc = ResourceNotFoundError("Not found")
        self.assertEqual(exc.status_code, status.HTTP_404_NOT_FOUND)


class ErrorLoggerTestCase(TestCase):
    """Test error logging utilities"""
    
    def test_log_service_error(self):
        """Test service error logging"""
        # Should not raise exception
        try:
            ErrorLogger.log_service_error(
                service_name='TestService',
                operation='test_operation',
                error=Exception('Test error'),
                context={'key': 'value'}
            )
        except Exception as e:
            self.fail(f"log_service_error raised exception: {e}")
    
    def test_log_external_service_error(self):
        """Test external service error logging"""
        # Should not raise exception
        try:
            ErrorLogger.log_external_service_error(
                service_name='ExternalAPI',
                operation='api_call',
                error=Exception('API error'),
                url='https://example.com'
            )
        except Exception as e:
            self.fail(f"log_external_service_error raised exception: {e}")
    
    def test_log_validation_error(self):
        """Test validation error logging"""
        # Should not raise exception
        try:
            ErrorLogger.log_validation_error(
                model_name='TestModel',
                field_errors={'field': ['Error message']},
                context={'user_id': 123}
            )
        except Exception as e:
            self.fail(f"log_validation_error raised exception: {e}")
    
    def test_log_rate_limit_exceeded(self):
        """Test rate limit logging"""
        # Should not raise exception
        try:
            ErrorLogger.log_rate_limit_exceeded(
                resource='test_resource',
                identifier='user_123',
                limit=10
            )
        except Exception as e:
            self.fail(f"log_rate_limit_exceeded raised exception: {e}")
