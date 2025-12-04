"""
Custom middleware for logging and monitoring
"""
import logging
import time
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all requests with timing information
    """
    
    def process_request(self, request):
        """Store request start time"""
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Log request details and timing"""
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            
            # Log request details
            log_data = {
                'method': request.method,
                'path': request.path,
                'status': response.status_code,
                'duration_ms': round(duration * 1000, 2),
                'user': request.user.id if request.user.is_authenticated else 'anonymous',
                'ip': self._get_client_ip(request),
            }
            
            # Log at different levels based on status code
            if response.status_code >= 500:
                logger.error(
                    "Request failed: %(method)s %(path)s - %(status)s - %(duration_ms)sms - User: %(user)s",
                    log_data
                )
            elif response.status_code >= 400:
                logger.warning(
                    "Request error: %(method)s %(path)s - %(status)s - %(duration_ms)sms - User: %(user)s",
                    log_data
                )
            else:
                logger.info(
                    "Request: %(method)s %(path)s - %(status)s - %(duration_ms)sms",
                    log_data
                )
        
        return response
    
    def process_exception(self, request, exception):
        """Log exceptions"""
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            
            logger.error(
                "Request exception: %s %s - %s - %.2fms - User: %s",
                request.method,
                request.path,
                exception.__class__.__name__,
                duration * 1000,
                request.user.id if request.user.is_authenticated else 'anonymous',
                exc_info=True
            )
        
        return None
    
    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware to monitor slow requests
    """
    
    SLOW_REQUEST_THRESHOLD = 1.0  # seconds
    
    def process_request(self, request):
        """Store request start time"""
        request._perf_start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Check for slow requests"""
        if hasattr(request, '_perf_start_time'):
            duration = time.time() - request._perf_start_time
            
            if duration > self.SLOW_REQUEST_THRESHOLD:
                logger.warning(
                    "Slow request detected: %s %s - %.2fs - Status: %s",
                    request.method,
                    request.path,
                    duration,
                    response.status_code
                )
        
        return response
