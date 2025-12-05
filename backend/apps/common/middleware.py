"""
Custom middleware for authentication and request handling
"""
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class AuthenticationDebugMiddleware(MiddlewareMixin):
    """
    Middleware to debug authentication issues by logging request headers
    """
    
    def process_request(self, request):
        """Log authentication-related headers for debugging"""
        # Only log for API endpoints
        if request.path.startswith('/api/'):
            auth_header = request.META.get('HTTP_AUTHORIZATION', 'NOT PRESENT')
            logger.debug(
                f"[Auth Debug] {request.method} {request.path} | "
                f"Auth header: {auth_header[:50] if auth_header != 'NOT PRESENT' else auth_header} | "
                f"User: {request.user if hasattr(request, 'user') else 'Not set yet'}"
            )
        return None
    
    def process_response(self, request, response):
        """Log authentication failures"""
        if request.path.startswith('/api/') and response.status_code == 401:
            logger.warning(
                f"[Auth Debug] 401 response for {request.method} {request.path} | "
                f"User authenticated: {request.user.is_authenticated if hasattr(request, 'user') else 'Unknown'}"
            )
        return response
