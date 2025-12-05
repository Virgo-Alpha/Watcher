# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of Watcher seriously. If you discover a security vulnerability, please follow these steps:

### 1. **Do Not** Open a Public Issue

Please do not report security vulnerabilities through public GitHub issues, discussions, or pull requests.

### 2. Report Privately

Send a detailed report to: **[your-security-email@example.com]**

Include:
- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Suggested fix (if any)

### 3. Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity (critical issues within 7 days)

### 4. Disclosure Policy

- We will acknowledge your report within 48 hours
- We will provide regular updates on our progress
- We will credit you in the security advisory (unless you prefer to remain anonymous)
- We request that you do not publicly disclose the vulnerability until we have released a fix

## Security Considerations

### SSRF Protection

Watcher accepts user-provided URLs for scraping. We have implemented multiple layers of protection:

1. **URL Validation**: Only HTTP/HTTPS protocols allowed
2. **Private IP Blocking**: Blocks RFC1918 ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
3. **Localhost Blocking**: Blocks 127.0.0.1, ::1, localhost
4. **Cloud Metadata Blocking**: Blocks 169.254.0.0/16 (AWS metadata endpoints)
5. **Reserved IP Blocking**: Blocks other reserved IP ranges

### Rate Limiting

The following endpoints have rate limits to prevent abuse:

- **Test Scrape**: 10 requests/minute per user
- **AI Config Generation**: 20 requests/minute per user
- **Manual Refresh**: 30 requests/minute per user

### Authentication

- JWT-based authentication with short-lived access tokens (15 minutes)
- Refresh tokens with 7-day expiration
- Owner-only access enforced on private haunts

### Browser Isolation

- Playwright browsers run in sandboxed containers
- Resource limits: 10MB max page size, 30s timeout
- Maximum 10 concurrent browser instances per worker

### Data Privacy

- No raw HTML storage (only normalized key-value state)
- Private haunts isolated by user ownership
- API keys never logged or exposed in responses

## Known Security Considerations

### Current Limitations

1. **Rate Limiting**: Needs implementation via Django REST Framework throttling or Redis
2. **Content Size Validation**: Should validate extracted content size before storage
3. **CSP Headers**: Content Security Policy headers recommended for frontend

### Recommended Security Practices

If you're self-hosting Watcher:

1. **Use HTTPS**: Always run behind HTTPS in production
2. **Rotate API Keys**: Regularly rotate Google Gemini API keys
3. **Monitor Logs**: Watch for suspicious scraping patterns
4. **Update Dependencies**: Keep Docker images and Python packages updated
5. **Firewall Rules**: Restrict outbound connections from scraping service
6. **Database Backups**: Regular encrypted backups
7. **Environment Variables**: Never commit `.env` files

## Security Testing

We welcome security researchers to test Watcher. Please:

- Test against your own instance (not production)
- Respect rate limits
- Report findings responsibly
- Do not access or modify other users' data

### Out of Scope

The following are considered out of scope:

- Denial of Service (DoS) attacks
- Social engineering attacks
- Physical attacks
- Issues in third-party dependencies (report to upstream)

## Security Updates

Security updates will be released as:

- **Critical**: Immediate patch release
- **High**: Patch within 7 days
- **Medium**: Patch in next minor release
- **Low**: Patch in next major release

Subscribe to GitHub releases to receive security notifications.

## Bug Bounty

We currently do not offer a bug bounty program. However, we deeply appreciate security researchers' contributions and will publicly acknowledge your findings (with your permission).

## Contact

For security concerns: **[your-security-email@example.com]**

For general questions: Open a GitHub issue

---

**Last Updated**: December 2024
