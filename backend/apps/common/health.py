"""
Health check utilities for system monitoring
"""
import logging
from typing import Dict, Any, Tuple
from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.db.utils import OperationalError

logger = logging.getLogger(__name__)


class HealthCheckService:
    """Service for performing system health checks"""
    
    @staticmethod
    def check_database() -> Tuple[bool, str]:
        """
        Check database connectivity
        
        Returns:
            Tuple of (is_healthy, message)
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return True, "Database connection OK"
        except OperationalError as e:
            logger.error(f"Database health check failed: {e}")
            return False, f"Database connection failed: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected database health check error: {e}")
            return False, f"Database check error: {str(e)}"
    
    @staticmethod
    def check_cache() -> Tuple[bool, str]:
        """
        Check Redis cache connectivity
        
        Returns:
            Tuple of (is_healthy, message)
        """
        try:
            # Try to set and get a test value
            test_key = 'health_check_test'
            test_value = 'ok'
            cache.set(test_key, test_value, timeout=10)
            retrieved_value = cache.get(test_key)
            
            if retrieved_value == test_value:
                cache.delete(test_key)
                return True, "Cache connection OK"
            else:
                return False, "Cache read/write mismatch"
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return False, f"Cache connection failed: {str(e)}"
    
    @staticmethod
    def check_celery() -> Tuple[bool, str]:
        """
        Check Celery worker connectivity
        
        Returns:
            Tuple of (is_healthy, message)
        """
        try:
            from celery import current_app
            
            # Check if workers are available
            inspect = current_app.control.inspect()
            stats = inspect.stats()
            
            if stats:
                worker_count = len(stats)
                return True, f"Celery OK ({worker_count} workers active)"
            else:
                return False, "No Celery workers available"
        except Exception as e:
            logger.error(f"Celery health check failed: {e}")
            return False, f"Celery check failed: {str(e)}"
    
    @staticmethod
    def check_ai_service() -> Tuple[bool, str]:
        """
        Check AI service availability
        
        Returns:
            Tuple of (is_healthy, message)
        """
        try:
            from apps.ai.services import AIConfigService
            
            service = AIConfigService()
            if service.is_available():
                return True, "AI service configured"
            else:
                return False, "AI service not configured (LLM_API_KEY missing)"
        except Exception as e:
            logger.error(f"AI service health check failed: {e}")
            return False, f"AI service check failed: {str(e)}"
    
    @staticmethod
    def check_browser_pool() -> Tuple[bool, str]:
        """
        Check browser pool availability
        
        Returns:
            Tuple of (is_healthy, message)
        """
        try:
            from apps.scraping.services import get_browser_pool
            
            pool = get_browser_pool()
            # Just check if pool exists, don't actually acquire a browser
            if pool:
                return True, "Browser pool initialized"
            else:
                return False, "Browser pool not available"
        except Exception as e:
            logger.error(f"Browser pool health check failed: {e}")
            return False, f"Browser pool check failed: {str(e)}"
    
    @classmethod
    def get_full_health_status(cls) -> Dict[str, Any]:
        """
        Get comprehensive health status of all system components
        
        Returns:
            Dictionary with health status of all components
        """
        checks = {
            'database': cls.check_database(),
            'cache': cls.check_cache(),
            'celery': cls.check_celery(),
            'ai_service': cls.check_ai_service(),
            'browser_pool': cls.check_browser_pool(),
        }
        
        # Determine overall health
        all_healthy = all(is_healthy for is_healthy, _ in checks.values())
        critical_healthy = checks['database'][0] and checks['cache'][0]
        
        # Build response
        status_dict = {
            'status': 'healthy' if all_healthy else ('degraded' if critical_healthy else 'unhealthy'),
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {
                name: {
                    'status': 'healthy' if is_healthy else 'unhealthy',
                    'message': message
                }
                for name, (is_healthy, message) in checks.items()
            }
        }
        
        return status_dict
    
    @classmethod
    def get_basic_health_status(cls) -> Dict[str, Any]:
        """
        Get basic health status (database and cache only)
        
        Returns:
            Dictionary with basic health status
        """
        db_healthy, db_message = cls.check_database()
        cache_healthy, cache_message = cls.check_cache()
        
        all_healthy = db_healthy and cache_healthy
        
        return {
            'status': 'healthy' if all_healthy else 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {
                'database': {
                    'status': 'healthy' if db_healthy else 'unhealthy',
                    'message': db_message
                },
                'cache': {
                    'status': 'healthy' if cache_healthy else 'unhealthy',
                    'message': cache_message
                }
            }
        }
