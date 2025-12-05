# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of Watcher seriously. If you discover a security vulnerability, please follow these steps:

### 1. Do Not Disclose Publicly

Please do not open a public GitHub issue for security vulnerabilities. This helps protect users while we work on a fix.

### 2. Report Privately

Send details to: **[your-security-email@example.com]**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### 3. Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity (critical issues within 7-14 days)

## Security Best Practices

### For Users

#### Environment Variables
- Never commit `.env` files to version control
- Use strong, unique values for `SECRET_KEY` and `JWT_SECRET`
- Rotate API keys regularly
- Use environment-specific configurations

#### API Keys
- Store Google Gemini API keys securely in `.env`
- Never expose API keys in client-side code
- Use rate limiting to prevent abuse
- Monitor API usage for anomalies

#### Authentication
- Use strong passwords (minimum 12 characters)
- Enable two-factor authentication when available
- Regularly review active sessions
- Use JWT tokens with appropriate expiration times

#### Docker Security
- Keep Docker images updated
- Use non-root users in containers
- Scan images for vulnerabilities regularly
- Limit container resource usage

### For Developers

#### Code Security
- Validate all user inputs
- Sanitize data before database queries
- Use parameterized queries (Django ORM handles this)
- Implement proper CORS policies
- Use HTTPS in production

#### Dependencies
- Regularly update dependencies
- Run `npm audit` and `pip-audit` regularly
- Review security advisories for used packages
- Pin dependency versions in production

#### Database Security
- Use strong PostgreSQL passwords
- Limit database user permissions
- Enable SSL for database connections in production
- Regular backups with encryption
- Never expose database ports publicly

#### Scraping Security
- Respect robots.txt and rate limits
- Implement request throttling
- Use user-agent identification
- Handle timeouts and errors gracefully
- Validate scraped content before storage

#### AI Integration Security
- Validate AI-generated configurations before execution
- Sanitize prompts to prevent injection attacks
- Implement rate limiting for AI API calls
- Handle API failures gracefully
- Never trust AI output without validation

## Known Security Considerations

### Playwright Browser Automation
- Runs in isolated containers
- No persistent browser state
- Sandboxed execution environment
- Regular Chromium updates required

### Public Haunt Subscriptions
- Public haunts expose configuration details
- Users should not include sensitive selectors
- Rate limiting prevents abuse
- Authentication required for modifications

### RSS Feed Generation
- Feeds are publicly accessible by design
- No authentication required for RSS endpoints
- Content sanitization prevents XSS
- Rate limiting prevents scraping abuse

## Security Headers

Production deployments should include:

```nginx
# Nginx configuration
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

## Vulnerability Disclosure Policy

We follow coordinated vulnerability disclosure:

1. **Report received** → Acknowledgment sent
2. **Validation** → Confirm vulnerability exists
3. **Fix development** → Create and test patch
4. **Release** → Deploy fix to production
5. **Public disclosure** → After users have time to update (typically 30 days)

## Security Updates

Security updates are released as:
- **Critical**: Immediate patch release
- **High**: Patch within 7 days
- **Medium**: Included in next minor release
- **Low**: Included in next major release

## Compliance

### Data Protection
- User data stored securely in PostgreSQL
- Passwords hashed with Django's PBKDF2
- JWT tokens for stateless authentication
- GDPR-compliant data export/deletion available

### Third-Party Services
- Google Gemini API: Subject to Google's privacy policy
- Scraped websites: Respect terms of service
- RSS feeds: Public by design

## Security Checklist for Deployment

- [ ] Change default `SECRET_KEY` and `JWT_SECRET`
- [ ] Set `DEBUG=False` in production
- [ ] Configure `ALLOWED_HOSTS` properly
- [ ] Use HTTPS with valid SSL certificates
- [ ] Enable database SSL connections
- [ ] Set up firewall rules (only expose 80/443)
- [ ] Configure rate limiting
- [ ] Enable security headers
- [ ] Set up monitoring and alerting
- [ ] Regular backup schedule
- [ ] Update dependencies regularly
- [ ] Review logs for suspicious activity

## Contact

For security concerns: **[your-security-email@example.com]**

For general issues: Use GitHub Issues

---

**Last Updated**: December 2025
