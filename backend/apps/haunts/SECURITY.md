# Security Considerations for Haunt Management

## SSRF Protection

The haunt management system accepts user-provided URLs for scraping. To prevent Server-Side Request Forgery (SSRF) attacks, the following protections have been implemented:

### URL Validation (`validators.py`)

The `URLSecurityValidator` class provides centralized URL validation:

1. **Scheme Restriction**: Only HTTP and HTTPS protocols are allowed
2. **Private IP Blocking**: Blocks RFC1918 private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
3. **Localhost Blocking**: Blocks 127.0.0.1, ::1, localhost, and similar variants
4. **Link-Local Blocking**: Blocks 169.254.0.0/16 (AWS metadata endpoints)
5. **Reserved IP Blocking**: Blocks other reserved IP ranges

### Affected Endpoints

The following endpoints accept URLs and MUST use `URLSecurityValidator`:

- `POST /api/v1/haunts/create_with_ai/` - AI-powered haunt creation
- `POST /api/v1/haunts/test_scrape/` - Test scraping preview
- `POST /api/v1/haunts/generate_config_preview/` - AI config generation

### Usage Example

```python
from .validators import URLSecurityValidator

# In view method
try:
    URLSecurityValidator.validate_url(url)
except serializers.ValidationError as e:
    return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
```

## Rate Limiting

**CRITICAL**: The following endpoints need rate limiting to prevent abuse:

### Recommended Rate Limits

1. **Test Scrape** (`test_scrape`):
   - 10 requests per minute per user
   - 100 requests per hour per user
   - Prevents resource exhaustion from concurrent browser instances

2. **AI Config Generation** (`create_with_ai`, `generate_config_preview`):
   - 20 requests per minute per user
   - 200 requests per hour per user
   - Prevents OpenAI API quota exhaustion and cost overruns

3. **Manual Refresh** (future `refresh` endpoint):
   - 30 requests per minute per user
   - Prevents scraping service overload

### Implementation Options

#### Option 1: Django REST Framework Throttling

```python
from rest_framework.throttling import UserRateThrottle

class TestScrapeThrottle(UserRateThrottle):
    rate = '10/min'

class HauntViewSet(viewsets.ModelViewSet):
    @action(detail=False, methods=['post'], throttle_classes=[TestScrapeThrottle])
    def test_scrape(self, request):
        # ...
```

#### Option 2: Redis-based Rate Limiting

```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='user', rate='10/m', method='POST')
def test_scrape(self, request):
    # ...
```

## Error Message Sanitization

Error messages have been sanitized to prevent information disclosure:

### Before (VULNERABLE)
```python
except Exception as e:
    return Response({'error': str(e)}, status=500)  # Exposes stack traces
```

### After (SECURE)
```python
except ScrapingError as e:
    logger.error(f"Test scrape failed: {e}")  # Log details
    return Response({
        'error': 'Failed to scrape the URL. Please check the URL and configuration.'
    }, status=400)  # Generic message to user
```

## Additional Security Recommendations

### 1. Playwright Browser Isolation

Ensure Playwright browsers run with proper sandboxing:

```python
browser = p.chromium.launch(
    headless=True,
    args=[
        '--no-sandbox',  # Only in Docker containers
        '--disable-dev-shm-usage',
        '--disable-gpu'
    ]
)
```

### 2. Resource Limits

Implement resource limits in `ScrapingService`:

- Maximum page size: 10MB
- Maximum scraping time: 30 seconds
- Maximum concurrent browsers: 10 per worker

### 3. Content Security

- Validate extracted content size before storage
- Sanitize HTML content if displayed in UI
- Implement CSP headers for frontend

### 4. API Key Protection

- Never log `LLM_API_KEY` or expose in error messages
- Use environment variables only
- Rotate keys regularly
- Monitor API usage for anomalies

### 5. Authentication & Authorization

All endpoints require authentication:
- JWT tokens with short expiration (15 minutes)
- Refresh tokens with longer expiration (7 days)
- Owner-only access to private haunts enforced by `IsOwnerOrReadOnly` permission

## Security Testing Checklist

- [ ] Test SSRF protection with private IPs (127.0.0.1, 192.168.1.1, 10.0.0.1)
- [ ] Test SSRF protection with cloud metadata endpoints (169.254.169.254)
- [ ] Test rate limiting on all scraping endpoints
- [ ] Verify error messages don't leak sensitive information
- [ ] Test authentication on all endpoints
- [ ] Verify folder/haunt ownership checks
- [ ] Test with malicious URLs (javascript:, file:, data:)
- [ ] Test with extremely large URLs (>2000 characters)
- [ ] Test concurrent scraping resource limits
- [ ] Verify OpenAI API key is never exposed in logs or responses

## Incident Response

If SSRF or other security issues are discovered:

1. Immediately disable affected endpoints
2. Review logs for exploitation attempts
3. Notify users if data was compromised
4. Apply patches and redeploy
5. Conduct security audit of similar code
