"""
Centralized error handling and response formatting
"""
import logging
import traceback
from typing import Any, Dict, Optional

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def format_error_response(
    error_code: str,
    message: str,
    details: Optional[Any] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST
) -> Dict[str, Any]:
    """
    Format a standardized error response
    
    Args:
        error_code: Machine-readable error code
        message: Human-readable error message
        details: Optional additional error details
        status_code: HTTP status code
        
    Returns:
        Formatted error response dictionary
    """
    response = {
        'error': {
            'code': error_code,
            'message': message,
            'status': status_code
        }
    }
    
    if details is not None:
        response['error']['details'] = details
    
    return response


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides standardized error responses
    
    Args:
        exc: The exception instance
        context: Context dictionary with view and request information
        
    Returns:
        Response object with formatted error
    """
    # Call DRF's default exception handler first
    response = drf_exception_handler(exc, context)
    
    # Get request information for logging
    request = context.get('request')
    view = context.get('view')
    
    # Log the exception with context
    log_exception(exc, request, view)
    
    # If DRF handled it, format the response
    if response is not None:
        error_code = getattr(exc, 'default_code', 'error')
        
        # Handle validation errors specially
        if isinstance(exc, (DRFValidationError, DjangoValidationError)):
            response.data = format_error_response(
                error_code='validation_error',
                message='Validation failed',
                details=response.data,
                status_code=response.status_code
            )
        else:
            # Format other API exceptions
            response.data = format_error_response(
                error_code=error_code,
                message=str(exc),
                details=response.data if isinstance(response.data, dict) else None,
                status_code=response.status_code
            )
        
        return response
    
    # Handle exceptions not caught by DRF
    if isinstance(exc, Http404):
        return Response(
            format_error_response(
                error_code='not_found',
                message='Resource not found',
                status_code=status.HTTP_404_NOT_FOUND
            ),
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Handle unexpected exceptions
    logger.error(
        "Unhandled exception in %s: %s",
        view.__class__.__name__ if view else 'Unknown',
        str(exc),
        exc_info=True
    )
    
    return Response(
        format_error_response(
            error_code='internal_error',
            message='An unexpected error occurred',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ),
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


def log_exception(exc, request=None, view=None):
    """
    Log exception with context information
    
    Args:
        exc: The exception instance
        request: Optional request object
        view: Optional view object
    """
    # Determine log level based on exception type
    if isinstance(exc, (Http404, APIException)) and exc.status_code < 500:
        log_level = logging.WARNING
    else:
        log_level = logging.ERROR
    
    # Build context information
    context_info = []
    
    if view:
        context_info.append(f"View: {view.__class__.__name__}")
    
    if request:
        context_info.append(f"Method: {request.method}")
        context_info.append(f"Path: {request.path}")
        if request.user and request.user.is_authenticated:
            context_info.append(f"User: {request.user.id}")
    
    context_str = " | ".join(context_info) if context_info else "No context"
    
    # Log the exception
    logger.log(
        log_level,
        "Exception occurred: %s | %s | Error: %s",
        exc.__class__.__name__,
        context_str,
        str(exc),
        exc_info=(log_level == logging.ERROR)
    )


class ErrorLogger:
    """
    Utility class for structured error logging
    """
    
    @staticmethod
    def log_service_error(
        service_name: str,
        operation: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Log a service-level error with structured information
        
        Args:
            service_name: Name of the service (e.g., 'ScrapingService')
            operation: Operation being performed (e.g., 'scrape_url')
            error: The exception that occurred
            context: Optional context dictionary
        """
        logger.error(
            "Service error in %s.%s: %s | Context: %s",
            service_name,
            operation,
            str(error),
            context or {},
            exc_info=True
        )
    
    @staticmethod
    def log_external_service_error(
        service_name: str,
        operation: str,
        error: Exception,
        url: Optional[str] = None
    ):
        """
        Log an external service error
        
        Args:
            service_name: Name of external service (e.g., 'OpenAI')
            operation: Operation being performed
            error: The exception that occurred
            url: Optional URL being accessed
        """
        logger.error(
            "External service error: %s.%s | URL: %s | Error: %s",
            service_name,
            operation,
            url or 'N/A',
            str(error),
            exc_info=True
        )
    
    @staticmethod
    def log_validation_error(
        model_name: str,
        field_errors: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Log a validation error
        
        Args:
            model_name: Name of the model being validated
            field_errors: Dictionary of field errors
            context: Optional context dictionary
        """
        logger.warning(
            "Validation error for %s: %s | Context: %s",
            model_name,
            field_errors,
            context or {}
        )
    
    @staticmethod
    def log_rate_limit_exceeded(
        resource: str,
        identifier: str,
        limit: int
    ):
        """
        Log a rate limit exceeded event
        
        Args:
            resource: Resource being rate limited
            identifier: Identifier (user ID, IP, etc.)
            limit: Rate limit that was exceeded
        """
        logger.warning(
            "Rate limit exceeded: Resource=%s | Identifier=%s | Limit=%s",
            resource,
            identifier,
            limit
        )
