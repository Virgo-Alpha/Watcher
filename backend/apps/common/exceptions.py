"""
Custom exception classes and error handling utilities
"""
from rest_framework import status
from rest_framework.exceptions import APIException


class ServiceUnavailableError(APIException):
    """Raised when an external service is unavailable"""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Service temporarily unavailable.'
    default_code = 'service_unavailable'


class RateLimitExceededError(APIException):
    """Raised when rate limit is exceeded"""
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = 'Rate limit exceeded. Please try again later.'
    default_code = 'rate_limit_exceeded'


class ValidationError(APIException):
    """Raised when validation fails"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Validation failed.'
    default_code = 'validation_error'


class ResourceNotFoundError(APIException):
    """Raised when a resource is not found"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Resource not found.'
    default_code = 'not_found'


class PermissionDeniedError(APIException):
    """Raised when permission is denied"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Permission denied.'
    default_code = 'permission_denied'


class ConfigurationError(APIException):
    """Raised when configuration is invalid"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'System configuration error.'
    default_code = 'configuration_error'


class ExternalServiceError(APIException):
    """Raised when external service call fails"""
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = 'External service error.'
    default_code = 'external_service_error'
