"""
Application metrics collection and monitoring utilities
"""
import logging
import time
from typing import Dict, Any, Optional
from functools import wraps
from datetime import datetime, timedelta

from django.core.cache import cache
from django.db import connection
from django.db.models import Count, Avg, Q
from django.utils import timezone

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects and stores application metrics for monitoring
    """
    
    # Cache keys for metrics
    SCRAPE_SUCCESS_KEY = 'metrics:scrape_success'
    SCRAPE_FAILURE_KEY = 'metrics:scrape_failure'
    SCRAPE_DURATION_KEY = 'metrics:scrape_duration'
    API_REQUEST_COUNT_KEY = 'metrics:api_requests'
    API_ERROR_COUNT_KEY = 'metrics:api_errors'
    
    # Metric retention period
    RETENTION_SECONDS = 3600  # 1 hour
    
    @classmethod
    def record_scrape_success(cls, haunt_id: str, duration_ms: float):
        """
        Record a successful scrape operation
        
        Args:
            haunt_id: ID of the haunt that was scraped
            duration_ms: Duration of the scrape in milliseconds
        """
        try:
            # Increment success counter
            cache_key = f"{cls.SCRAPE_SUCCESS_KEY}:{haunt_id}"
            current = cache.get(cache_key, 0)
            cache.set(cache_key, current + 1, cls.RETENTION_SECONDS)
            
            # Record duration
            duration_key = f"{cls.SCRAPE_DURATION_KEY}:{haunt_id}"
            durations = cache.get(duration_key, [])
            durations.append(duration_ms)
            # Keep only last 100 durations
            if len(durations) > 100:
                durations = durations[-100:]
            cache.set(duration_key, durations, cls.RETENTION_SECONDS)
            
            logger.debug(f"Recorded scrape success for haunt {haunt_id}: {duration_ms}ms")
        except Exception as e:
            logger.error(f"Failed to record scrape success metric: {e}")
    
    @classmethod
    def record_scrape_failure(cls, haunt_id: str, error_type: str):
        """
        Record a failed scrape operation
        
        Args:
            haunt_id: ID of the haunt that failed to scrape
            error_type: Type of error that occurred
        """
        try:
            # Increment failure counter
            cache_key = f"{cls.SCRAPE_FAILURE_KEY}:{haunt_id}"
            current = cache.get(cache_key, 0)
            cache.set(cache_key, current + 1, cls.RETENTION_SECONDS)
            
            logger.warning(f"Recorded scrape failure for haunt {haunt_id}: {error_type}")
        except Exception as e:
            logger.error(f"Failed to record scrape failure metric: {e}")
    
    @classmethod
    def record_api_request(cls, endpoint: str, method: str, status_code: int, duration_ms: float):
        """
        Record an API request
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            status_code: Response status code
            duration_ms: Request duration in milliseconds
        """
        try:
            # Increment request counter
            cache_key = f"{cls.API_REQUEST_COUNT_KEY}:{method}:{endpoint}"
            current = cache.get(cache_key, 0)
            cache.set(cache_key, current + 1, cls.RETENTION_SECONDS)
            
            # Record errors
            if status_code >= 400:
                error_key = f"{cls.API_ERROR_COUNT_KEY}:{method}:{endpoint}"
                current_errors = cache.get(error_key, 0)
                cache.set(error_key, current_errors + 1, cls.RETENTION_SECONDS)
            
            logger.debug(f"Recorded API request: {method} {endpoint} - {status_code} - {duration_ms}ms")
        except Exception as e:
            logger.error(f"Failed to record API request metric: {e}")
    
    @classmethod
    def get_scrape_metrics(cls, haunt_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get scraping metrics
        
        Args:
            haunt_id: Optional haunt ID to filter metrics
            
        Returns:
            Dictionary of scraping metrics
        """
        if haunt_id:
            success_key = f"{cls.SCRAPE_SUCCESS_KEY}:{haunt_id}"
            failure_key = f"{cls.SCRAPE_FAILURE_KEY}:{haunt_id}"
            duration_key = f"{cls.SCRAPE_DURATION_KEY}:{haunt_id}"
            
            success_count = cache.get(success_key, 0)
            failure_count = cache.get(failure_key, 0)
            durations = cache.get(duration_key, [])
            
            total = success_count + failure_count
            success_rate = (success_count / total * 100) if total > 0 else 0
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            return {
                'haunt_id': haunt_id,
                'success_count': success_count,
                'failure_count': failure_count,
                'total_count': total,
                'success_rate': round(success_rate, 2),
                'avg_duration_ms': round(avg_duration, 2),
                'min_duration_ms': round(min(durations), 2) if durations else 0,
                'max_duration_ms': round(max(durations), 2) if durations else 0,
            }
        else:
            # Return aggregate metrics (would need to iterate all haunts)
            return {
                'message': 'Aggregate metrics not implemented. Provide haunt_id for specific metrics.'
            }
    
    @classmethod
    def get_database_metrics(cls) -> Dict[str, Any]:
        """
        Get database performance metrics
        
        Returns:
            Dictionary of database metrics
        """
        try:
            from apps.haunts.models import Haunt
            from apps.rss.models import RSSItem
            
            # Get query counts from Django's connection
            query_count = len(connection.queries) if connection.queries_logged else 0
            
            # Get model counts
            haunt_count = Haunt.objects.count()
            rss_item_count = RSSItem.objects.count()
            
            # Get recent activity
            recent_haunts = Haunt.objects.filter(
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            recent_items = RSSItem.objects.filter(
                pub_date__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            return {
                'query_count': query_count,
                'total_haunts': haunt_count,
                'total_rss_items': rss_item_count,
                'haunts_created_24h': recent_haunts,
                'items_created_24h': recent_items,
            }
        except Exception as e:
            logger.error(f"Failed to get database metrics: {e}")
            return {'error': str(e)}


class PerformanceMonitor:
    """
    Monitor and track performance of operations
    """
    
    @staticmethod
    def monitor_operation(operation_name: str):
        """
        Decorator to monitor operation performance
        
        Args:
            operation_name: Name of the operation being monitored
            
        Usage:
            @PerformanceMonitor.monitor_operation('scrape_haunt')
            def scrape_haunt(haunt_id):
                # ... operation code ...
                pass
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                error_occurred = False
                error_type = None
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    error_occurred = True
                    error_type = e.__class__.__name__
                    raise
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Log performance
                    if error_occurred:
                        logger.warning(
                            f"Operation '{operation_name}' failed after {duration_ms:.2f}ms: {error_type}"
                        )
                    elif duration_ms > 1000:  # Log slow operations (>1s)
                        logger.warning(
                            f"Slow operation '{operation_name}' completed in {duration_ms:.2f}ms"
                        )
                    else:
                        logger.debug(
                            f"Operation '{operation_name}' completed in {duration_ms:.2f}ms"
                        )
            
            return wrapper
        return decorator
    
    @staticmethod
    def track_query_performance():
        """
        Context manager to track database query performance
        
        Usage:
            with PerformanceMonitor.track_query_performance():
                # ... database operations ...
                pass
        """
        class QueryTracker:
            def __enter__(self):
                self.start_query_count = len(connection.queries)
                self.start_time = time.time()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                query_count = len(connection.queries) - self.start_query_count
                duration_ms = (time.time() - self.start_time) * 1000
                
                if query_count > 10:
                    logger.warning(
                        f"High query count detected: {query_count} queries in {duration_ms:.2f}ms"
                    )
                elif duration_ms > 100:
                    logger.warning(
                        f"Slow database operation: {query_count} queries in {duration_ms:.2f}ms"
                    )
                else:
                    logger.debug(
                        f"Database operation: {query_count} queries in {duration_ms:.2f}ms"
                    )
        
        return QueryTracker()


class AlertManager:
    """
    Manage system alerts and notifications
    """
    
    # Alert thresholds
    HIGH_ERROR_RATE_THRESHOLD = 0.5  # 50% error rate
    SLOW_RESPONSE_THRESHOLD = 2000  # 2 seconds
    HIGH_QUERY_COUNT_THRESHOLD = 50
    
    @classmethod
    def check_scrape_health(cls, haunt_id: str) -> Optional[Dict[str, Any]]:
        """
        Check scraping health and return alert if needed
        
        Args:
            haunt_id: ID of the haunt to check
            
        Returns:
            Alert dictionary if alert should be raised, None otherwise
        """
        metrics = MetricsCollector.get_scrape_metrics(haunt_id)
        
        if metrics.get('total_count', 0) < 5:
            # Not enough data to determine health
            return None
        
        success_rate = metrics.get('success_rate', 100)
        
        if success_rate < (1 - cls.HIGH_ERROR_RATE_THRESHOLD) * 100:
            return {
                'severity': 'high',
                'type': 'high_error_rate',
                'message': f"High error rate for haunt {haunt_id}: {success_rate:.1f}% success rate",
                'metrics': metrics
            }
        
        avg_duration = metrics.get('avg_duration_ms', 0)
        if avg_duration > cls.SLOW_RESPONSE_THRESHOLD:
            return {
                'severity': 'medium',
                'type': 'slow_scraping',
                'message': f"Slow scraping for haunt {haunt_id}: {avg_duration:.0f}ms average",
                'metrics': metrics
            }
        
        return None
    
    @classmethod
    def check_system_health(cls) -> list:
        """
        Check overall system health and return alerts
        
        Returns:
            List of alert dictionaries
        """
        alerts = []
        
        try:
            # Check database metrics
            db_metrics = MetricsCollector.get_database_metrics()
            
            if 'error' in db_metrics:
                alerts.append({
                    'severity': 'critical',
                    'type': 'database_error',
                    'message': f"Database metrics collection failed: {db_metrics['error']}"
                })
            
            # Check for high query counts
            query_count = db_metrics.get('query_count', 0)
            if query_count > cls.HIGH_QUERY_COUNT_THRESHOLD:
                alerts.append({
                    'severity': 'medium',
                    'type': 'high_query_count',
                    'message': f"High database query count: {query_count} queries"
                })
        
        except Exception as e:
            logger.error(f"Failed to check system health: {e}")
            alerts.append({
                'severity': 'critical',
                'type': 'health_check_error',
                'message': f"Health check failed: {str(e)}"
            })
        
        return alerts
