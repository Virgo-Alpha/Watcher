# Monitoring and Error Handling Implementation

This document summarizes the comprehensive error handling, logging, and monitoring features added to the Watcher application.

## Overview

Task 11 "Add comprehensive testing and error handling" has been fully implemented with three main components:

1. **Error Handling and Logging** (Task 11.1)
2. **Comprehensive Test Suite** (Task 11.2)
3. **Monitoring and Observability** (Task 11.3)

## 1. Error Handling and Logging (Task 11.1)

### Custom Exception Classes

Created standardized exception classes in `apps/common/exceptions.py`:

- `ServiceUnavailableError` - For unavailable external services (503)
- `RateLimitExceededError` - For rate limit violations (429)
- `ValidationError` - For validation failures (400)
- `ResourceNotFoundError` - For missing resources (404)
- `PermissionDeniedError` - For permission violations (403)
- `ConfigurationError` - For configuration issues (500)
- `ExternalServiceError` - For external service failures (502)

### Centralized Error Handling

Implemented custom exception handler in `apps/common/error_handlers.py`:

- **Standardized Error Responses**: All errors follow consistent JSON format
- **Automatic Error Logging**: All exceptions logged with context
- **Error Logger Utility**: Structured logging for different error types

Error response format:
```json
{
  "error": {
    "code": "error_code",
    "message": "Human-readable message",
    "status": 400,
    "details": {}
  }
}
```

### Enhanced Logging Configuration

Updated `settings/base.py` with comprehensive logging:

- **Multiple Handlers**: Console, file error, file debug
- **Log Rotation**: 10MB files with 5 backups
- **Structured Logging**: JSON format option for production
- **Per-App Logging**: Separate log levels for different apps

Log files:
- `logs/error.log` - ERROR level logs
- `logs/debug.log` - DEBUG level logs (dev only)

### Request Logging Middleware

Created optional middleware in `apps/common/middleware.py`:

- **RequestLoggingMiddleware**: Logs all requests with timing
- **PerformanceMonitoringMiddleware**: Detects slow requests (>1s)

### Health Check Endpoints

Implemented comprehensive health checks in `apps/common/health.py`:

- `GET /health/` - Basic health check (database + cache)
- `GET /health/detailed/` - Detailed health check (all components)
- `GET /health/ready/` - Kubernetes readiness probe
- `GET /health/live/` - Kubernetes liveness probe

Health checks monitor:
- Database connectivity
- Redis cache connectivity
- Celery worker availability
- AI service configuration
- Browser pool initialization

## 2. Comprehensive Test Suite (Task 11.2)

### Test Coverage

Created minimal tests for new functionality in `apps/common/tests/`:

- **test_health.py**: Tests for health check endpoints
  - Basic health check
  - Detailed health check
  - Readiness check
  - Liveness check

- **test_error_handlers.py**: Tests for error handling
  - Error response formatting
  - Custom exception classes
  - Error logger utilities

### Existing Test Coverage

The application already has comprehensive test coverage:

- **AI Service Tests**: 15+ tests for configuration generation and summaries
- **Scraping Tests**: Tests for browser management, content extraction, change detection
- **Celery Task Tests**: Tests for scheduled scraping and task execution
- **API Tests**: Tests for haunts, folders, subscriptions, RSS feeds
- **Integration Tests**: End-to-end workflow tests

## 3. Monitoring and Observability (Task 11.3)

### Metrics Collection

Implemented comprehensive metrics in `apps/common/metrics.py`:

**MetricsCollector** tracks:
- Scrape success/failure counts
- Scrape duration statistics
- API request counts
- API error counts
- Database metrics

**PerformanceMonitor** provides:
- Operation performance decorator
- Database query performance tracking
- Slow operation detection

**AlertManager** monitors:
- High error rates (>50%)
- Slow scraping (>2s average)
- High query counts (>50 queries)
- System health issues

### Metrics Endpoint

Created `/metrics/` endpoint for monitoring:

```bash
# Get overall metrics
GET /metrics/

# Get metrics for specific haunt
GET /metrics/?haunt_id=<haunt_id>
```

Returns:
- Scrape metrics (success rate, duration, counts)
- Database metrics (query count, model counts)
- System alerts (performance issues, errors)

### Integration with Scraping

Updated `apps/scraping/tasks.py` to collect metrics:

- Records scrape success with duration
- Records scrape failures with error type
- Tracks scrape performance over time

### Monitoring Integration

The system is ready for integration with:

- **Load Balancers**: Health check endpoints
- **Kubernetes**: Readiness and liveness probes
- **Prometheus**: Metrics endpoint for scraping
- **Grafana**: Dashboard visualization
- **Alerting Systems**: Alert manager integration

## Configuration

### Enable Request Logging Middleware

Uncomment in `settings/base.py`:

```python
MIDDLEWARE = [
    # ...
    'apps.common.middleware.RequestLoggingMiddleware',
    'apps.common.middleware.PerformanceMonitoringMiddleware',
]
```

### Configure Log Files

Logs are stored in `backend/logs/`:
- Automatically rotated at 10MB
- 5 backup files retained
- Excluded from git via `.gitignore`

### Health Check Configuration

Health checks are automatically available at:
- `/health/` - Basic check
- `/health/detailed/` - Full check
- `/health/ready/` - Readiness
- `/health/live/` - Liveness
- `/metrics/` - Application metrics

## Usage Examples

### Error Handling

```python
from apps.common.exceptions import ServiceUnavailableError
from apps.common.error_handlers import ErrorLogger

# Raise custom exception
if not service.is_available():
    raise ServiceUnavailableError("AI service is unavailable")

# Log structured errors
ErrorLogger.log_service_error(
    service_name='ScrapingService',
    operation='scrape_url',
    error=exception,
    context={'url': url, 'haunt_id': haunt_id}
)
```

### Metrics Collection

```python
from apps.common.metrics import MetricsCollector, PerformanceMonitor

# Record metrics
MetricsCollector.record_scrape_success(haunt_id, duration_ms)
MetricsCollector.record_scrape_failure(haunt_id, 'TimeoutError')

# Monitor performance
@PerformanceMonitor.monitor_operation('scrape_haunt')
def scrape_haunt(haunt_id):
    # ... operation code ...
    pass
```

### Health Checks

```python
from apps.common.health import HealthCheckService

# Check individual components
db_healthy, db_message = HealthCheckService.check_database()
cache_healthy, cache_message = HealthCheckService.check_cache()

# Get full health status
health_status = HealthCheckService.get_full_health_status()
```

## Benefits

1. **Improved Debugging**: Structured logging with context makes debugging easier
2. **Better Monitoring**: Metrics and health checks enable proactive monitoring
3. **Consistent Errors**: Standardized error responses improve API usability
4. **Performance Tracking**: Automatic performance monitoring detects issues
5. **Production Ready**: Health checks and metrics enable production deployment
6. **Alert Management**: Automatic alerting for system issues

## Next Steps

1. **Set up Prometheus**: Configure Prometheus to scrape `/metrics/` endpoint
2. **Create Dashboards**: Build Grafana dashboards for visualization
3. **Configure Alerts**: Set up alerting rules for critical issues
4. **Enable Middleware**: Uncomment request logging middleware if needed
5. **Monitor Logs**: Set up log aggregation (e.g., ELK stack)

## Documentation

For detailed documentation, see:
- `backend/apps/common/README.md` - Complete feature documentation
- `backend/apps/common/` - Source code with inline documentation
- Health check endpoints - Self-documenting via API responses
