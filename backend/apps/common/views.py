"""
Common views including health check endpoints
"""
import logging
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .health import HealthCheckService

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Basic health check endpoint for load balancers and monitoring
    
    Returns 200 if database and cache are healthy, 503 otherwise
    """
    health_status = HealthCheckService.get_basic_health_status()
    
    if health_status['status'] == 'healthy':
        return Response(health_status, status=status.HTTP_200_OK)
    else:
        return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check_detailed(request):
    """
    Detailed health check endpoint with all system components
    
    Returns comprehensive health status of all services
    """
    health_status = HealthCheckService.get_full_health_status()
    
    # Return 200 for healthy or degraded, 503 for unhealthy
    if health_status['status'] in ['healthy', 'degraded']:
        return Response(health_status, status=status.HTTP_200_OK)
    else:
        return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([AllowAny])
def readiness_check(request):
    """
    Kubernetes-style readiness check
    
    Returns 200 if service is ready to accept traffic
    """
    db_healthy, _ = HealthCheckService.check_database()
    cache_healthy, _ = HealthCheckService.check_cache()
    
    if db_healthy and cache_healthy:
        return Response({'status': 'ready'}, status=status.HTTP_200_OK)
    else:
        return Response({'status': 'not_ready'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([AllowAny])
def liveness_check(request):
    """
    Kubernetes-style liveness check
    
    Returns 200 if service is alive (always returns 200 unless server is down)
    """
    return Response({'status': 'alive'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def metrics(request):
    """
    Application metrics endpoint
    
    Returns various application metrics for monitoring
    """
    from .metrics import MetricsCollector, AlertManager
    
    # Get haunt_id from query params if provided
    haunt_id = request.query_params.get('haunt_id')
    
    metrics_data = {
        'timestamp': timezone.now().isoformat(),
    }
    
    # Get scrape metrics
    if haunt_id:
        metrics_data['scrape_metrics'] = MetricsCollector.get_scrape_metrics(haunt_id)
        
        # Check for alerts
        alert = AlertManager.check_scrape_health(haunt_id)
        if alert:
            metrics_data['alerts'] = [alert]
    
    # Get database metrics
    metrics_data['database_metrics'] = MetricsCollector.get_database_metrics()
    
    # Get system alerts
    system_alerts = AlertManager.check_system_health()
    if system_alerts:
        if 'alerts' in metrics_data:
            metrics_data['alerts'].extend(system_alerts)
        else:
            metrics_data['alerts'] = system_alerts
    
    return Response(metrics_data, status=status.HTTP_200_OK)
