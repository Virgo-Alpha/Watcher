# Common App

This app provides shared utilities, error handling, and monitoring functionality for the Watcher application.

## Features

### Error Handling

The common app provides standardized error handling across all API endpoints:

- **Custom Exception Classes**: Predefined exception types for common scenarios
- **Standardized Error Responses**: Consistent JSON error format
- **Automatic Error Logging**: All exceptions are logged with context

#### Custom Exceptions

```python
from apps.common.exceptions import (
    ServiceUnavailableError,
    RateLimitExceededError,
    ValidationError,
    ResourceNotFoundError,
    PermissionDeniedError,
    ConfigurationError,
    ExternalServiceError
)

# Usage example
if not service.is_available():
    raise ServiceUnavailableError("AI service is currently unavailable")
```

#### Error Response Format

All errors follow this standardized format:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Validation failed",
    "status": 400,
    "details": {
      "field_name": ["Error message"]
    }
  }
}
```

#### Error Logging

Use the `ErrorLogger` utility for structured error logging:

```python
from apps.common.error_handlers import ErrorLogger

# Log service errors
ErrorLogger.log_service_error(
    service_name='ScrapingService',
    operation='scrape_url',
    error=exception,
    context={'url': url, 'haunt_id': haunt_id}
)

# Log external service errors
ErrorLogger.log_external_service_error(
    service_name='OpenAI',
    operation='generate_config',
    error=exception,
    url=api_url
)

# Log validation errors
ErrorLogger.log_validation_error(
    model_name='Haunt',
    field_errors={'url': ['Invalid URL format']},
    context={'user_id': user.id}
)

# Log rate limit events
ErrorLogger.log_rate_limit_exceeded(
    resource='manual_refresh',
    identifier=str(haunt.id),
    limit=1
)
```

### Health Check Endpoints

The common app provides health check endpoints for monitoring:

#### Endpoints

- `GET /health/` - Basic health check (database + cache)
- `GET /health/detailed/` - Detailed health check (all components)
- `GET /health/ready/` - Kubernetes readiness probe
- `GET /health/live/` - Kubernetes liveness probe

#### Basic Health Check

Returns 200 if database and cache are healthy:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "checks": {
    "database": {
      "status": "healthy",
      "message": "Database connection OK"
    },
    "cache": {
      "status": "healthy",
      "message": "Cache connection OK"
    }
  }
}
```

#### Detailed Health Check

Returns comprehensive status of all components:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "checks": {
    "database": {
      "status": "healthy",
      "message": "Database connection OK"
    },
    "cache": {
      "status": "healthy",
      "message": "Cache connection OK"
    },
    "celery": {
      "status": "healthy",
      "message": "Celery OK (3 workers active)"
    },
    "ai_service": {
      "status": "healthy",
      "message": "AI service configured"
    },
    "browser_pool": {
      "status": "healthy",
      "message": "Browser pool initialized"
    }
  }
}
```

### Middleware

Optional middleware for request logging and performance monitoring:

#### RequestLoggingMiddleware

Logs all requests with timing information:

```
INFO Request: GET /api/v1/haunts/ - 200 - 45.23ms
WARNING Request error: POST /api/v1/haunts/ - 400 - 12.45ms - User: 123
ERROR Request failed: GET /api/v1/haunts/invalid/ - 500 - 234.56ms - User: 123
```

#### PerformanceMonitoringMiddleware

Logs slow requests (>1 second):

```
WARNING Slow request detected: GET /api/v1/haunts/ - 1.23s - Status: 200
```

To enable middleware, uncomment in `settings/base.py`:

```python
MIDDLEWARE = [
    # ...
    'apps.common.middleware.RequestLoggingMiddleware',
    'apps.common.middleware.PerformanceMonitoringMiddleware',
]
```

## Configuration

### Logging

The app uses Django's logging framework with multiple handlers:

- **Console Handler**: All logs to stdout (for Docker)
- **File Error Handler**: ERROR level logs to `logs/error.log`
- **File Debug Handler**: DEBUG level logs to `logs/debug.log` (dev only)

Log files are automatically rotated at 10MB with 5 backups.

### Health Check Service

The `HealthCheckService` can be used programmatically:

```python
from apps.common.health import HealthCheckService

# Check individual components
db_healthy, db_message = HealthCheckService.check_database()
cache_healthy, cache_message = HealthCheckService.check_cache()

# Get full health status
health_status = HealthCheckService.get_full_health_status()
```

## Testing

Health checks and error handling can be tested:

```python
from apps.common.health import HealthCheckService
from apps.common.exceptions import ServiceUnavailableError

def test_health_check():
    status = HealthCheckService.get_basic_health_status()
    assert status['status'] in ['healthy', 'unhealthy']

def test_custom_exception():
    with pytest.raises(ServiceUnavailableError):
        raise ServiceUnavailableError("Service down")
```

## Metrics and Monitoring

The common app provides comprehensive metrics collection and monitoring:

### Metrics Collection

The `MetricsCollector` class tracks various application metrics:

```python
from apps.common.metrics import MetricsCollector

# Record scrape success
MetricsCollector.record_scrape_success(haunt_id, duration_ms)

# Record scrape failure
MetricsCollector.record_scrape_failure(haunt_id, error_type)

# Record API request
MetricsCollector.record_api_request(endpoint, method, status_code, duration_ms)

# Get metrics
metrics = MetricsCollector.get_scrape_metrics(haunt_id)
db_metrics = MetricsCollector.get_database_metrics()
```

### Metrics Endpoint

Access metrics via the `/metrics/` endpoint:

```bash
# Get overall metrics
GET /metrics/

# Get metrics for specific haunt
GET /metrics/?haunt_id=<haunt_id>
```

Response format:

```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "scrape_metrics": {
    "haunt_id": "123e4567-e89b-12d3-a456-426614174000",
    "success_count": 95,
    "failure_count": 5,
    "total_count": 100,
    "success_rate": 95.0,
    "avg_duration_ms": 234.56,
    "min_duration_ms": 123.45,
    "max_duration_ms": 567.89
  },
  "database_metrics": {
    "query_count": 12,
    "total_haunts": 150,
    "total_rss_items": 1234,
    "haunts_created_24h": 5,
    "items_created_24h": 45
  },
  "alerts": [
    {
      "severity": "medium",
      "type": "slow_scraping",
      "message": "Slow scraping for haunt 123: 2500ms average"
    }
  ]
}
```

### Performance Monitoring

Use the `PerformanceMonitor` decorator to track operation performance:

```python
from apps.common.metrics import PerformanceMonitor

@PerformanceMonitor.monitor_operation('scrape_haunt')
def scrape_haunt(haunt_id):
    # ... operation code ...
    pass

# Track database query performance
with PerformanceMonitor.track_query_performance():
    # ... database operations ...
    pass
```

### Alert Management

The `AlertManager` checks system health and raises alerts:

```python
from apps.common.metrics import AlertManager

# Check scrape health for a haunt
alert = AlertManager.check_scrape_health(haunt_id)

# Check overall system health
alerts = AlertManager.check_system_health()
```

Alert types:
- `high_error_rate`: Scraping error rate exceeds 50%
- `slow_scraping`: Average scrape duration exceeds 2 seconds
- `high_query_count`: Database query count exceeds 50
- `database_error`: Database metrics collection failed

## Monitoring Integration

The health check endpoints are designed to work with:

- **Load Balancers**: Use `/health/` for health checks
- **Kubernetes**: Use `/health/ready/` and `/health/live/` for probes
- **Monitoring Tools**: Use `/health/detailed/` for comprehensive status
- **Metrics Systems**: Use `/metrics/` for application metrics

Example Kubernetes configuration:

```yaml
livenessProbe:
  httpGet:
    path: /health/live/
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready/
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

Example Prometheus scrape config:

```yaml
scrape_configs:
  - job_name: 'watcher'
    metrics_path: '/metrics/'
    static_configs:
      - targets: ['localhost:8000']
```
