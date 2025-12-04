# Watcher - Site Change Monitoring

A containerized web application that monitors websites for user-defined changes using AI-powered configuration and provides RSS feeds with a Google Reader-style interface.

## Quick Start

1. Clone the repository
2. Copy environment variables:
   ```bash
   cp .env.example .env
   ```
3. Configure your OpenAI API key in `.env`:
   ```bash
   LLM_API_KEY=your-openai-api-key-here
   ```
4. Start all services:
   ```bash
   docker-compose up -d
   ```
5. Run initial migrations:
   ```bash
   docker-compose exec web python manage.py migrate
   ```
6. Create a superuser:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

## Services

- **Frontend**: React application (http://localhost:3000)
- **Backend**: Django REST API (http://localhost:8000)
- **Database**: PostgreSQL (localhost:5432)
- **Redis**: Message broker and cache (localhost:6379)
- **Celery**: Background task processing
- **Scheduler**: Celery beat for periodic tasks

## Key Features

### AI-Powered Configuration
- **Natural Language Setup**: Describe what you want to monitor in plain English
- **Automatic Selector Generation**: AI converts descriptions to CSS selectors and XPath expressions
- **Configuration Preview**: Generate and preview configurations before creating haunts
- **Test Scraping**: Test your configuration against live sites before saving
- **Configuration Validation**: Built-in validation ensures generated configurations are reliable
- **Change Summaries**: AI generates human-readable summaries of detected changes

### Monitoring Capabilities
- **SPA Compatible**: Uses Playwright headless browser for modern JavaScript applications
- **Flexible Scheduling**: Monitor sites every 15 minutes, 30 minutes, hourly, or daily
- **Smart Change Detection**: Configurable alert modes (once vs on-change)
- **RSS Integration**: Generates RSS feeds for easy integration with feed readers
- **Folder Organization**: Group related haunts into hierarchical folders
- **Public Sharing**: Share your monitoring configurations with the community

## Configuration

### Required Environment Variables

The application requires several environment variables to be configured in your `.env` file:

- `LLM_API_KEY` - **Required**: Your OpenAI API key for AI-powered haunt configuration
- `DATABASE_URL` - PostgreSQL connection string (default: `postgresql://postgres:postgres@db:5432/watcher`)
- `REDIS_URL` - Redis connection for Celery (default: `redis://redis:6379/0`)
- `SECRET_KEY` - Django secret key for security
- `DEBUG` - Set to `True` for development, `False` for production

### OpenAI API Setup

1. Create an account at [OpenAI](https://platform.openai.com/)
2. Generate an API key from your dashboard
3. Add the key to your `.env` file as `LLM_API_KEY=your-key-here`
4. The application uses OpenAI's GPT-3.5-turbo model for:
   - Converting natural language descriptions into CSS selectors and scraping configurations
   - Generating human-readable summaries of detected changes
   - Validating and optimizing monitoring configurations

**Note**: The AI service includes fallback functionality when the API is unavailable, but the natural language configuration feature requires a valid OpenAI API key.

## Development

### Backend Development
```bash
# View Django logs
docker-compose logs -f web

# Run Django commands
docker-compose exec web python manage.py <command>

# Run tests
docker-compose exec web python manage.py test
```

### Frontend Development
```bash
# View React logs
docker-compose logs -f frontend

# Install new packages
docker-compose exec frontend npm install <package>

# Run frontend tests
docker-compose exec frontend npm test
```

### Background Tasks
```bash
# Monitor Celery workers
docker-compose logs -f celery

# Monitor scheduled tasks
docker-compose logs -f scheduler
```

## Troubleshooting

### AI Service Issues

If you encounter issues with AI-powered configuration generation:

1. **Check API Key**: Ensure your OpenAI API key is correctly set in `.env`
   ```bash
   docker-compose exec web python manage.py shell -c "from apps.ai.services import AIConfigService; print('AI Available:', AIConfigService().is_available())"
   ```

2. **View AI Service Logs**: Check for API errors or rate limiting
   ```bash
   docker-compose logs -f web | grep -i "ai\|openai\|llm"
   ```

3. **Fallback Mode**: The application will work without AI for manual configuration, but natural language setup requires a valid API key

### Common Issues

- **Port Conflicts**: If ports 3000, 8000, 5432, or 6379 are in use, modify `docker-compose.yml`
- **Database Connection**: Ensure PostgreSQL container is healthy before running migrations
- **Celery Tasks**: Check Redis connection if background tasks aren't processing
```

## API Endpoints

### Haunt Management

#### Create Haunt with AI
```http
POST /api/v1/haunts/create_with_ai/
Content-Type: application/json

{
  "url": "https://example.com",
  "description": "Monitor the admission status",
  "name": "Optional name",
  "folder": "folder-uuid",
  "scrape_interval": 60,
  "alert_mode": "on_change"
}
```

Creates a haunt using AI to generate the configuration from natural language. The AI service analyzes the URL and description to create appropriate CSS selectors and scraping rules.

#### Generate Configuration Preview
```http
POST /api/v1/haunts/generate_config_preview/
Content-Type: application/json

{
  "url": "https://example.com",
  "description": "Monitor the admission status"
}
```

Generates a configuration preview without creating a haunt. Useful for the setup wizard to show users what will be monitored before they commit.

#### Test Scrape
```http
POST /api/v1/haunts/test_scrape/
Content-Type: application/json

{
  "url": "https://example.com",
  "config": {
    "selectors": {...},
    "normalization": {...},
    "truthy_values": {...}
  }
}
```

Performs a test scrape with the provided configuration and returns extracted data. Allows users to validate their configuration before creating a haunt.

### Folder Management

#### Get Folder Tree
```http
GET /api/v1/folders/tree/
```

Returns the complete folder hierarchy with nested children.

#### Assign Haunts to Folder
```http
POST /api/v1/folders/{folder_id}/assign_haunts/
Content-Type: application/json

{
  "haunt_ids": ["haunt-uuid-1", "haunt-uuid-2"]
}
```

### Security Features

All endpoints that accept URLs include SSRF (Server-Side Request Forgery) protection:
- Only HTTP and HTTPS schemes are allowed
- Private IP addresses and localhost are blocked
- URL validation prevents malicious requests

## Architecture

- **Backend**: Django REST Framework with PostgreSQL
- **Frontend**: React with Redux Toolkit
- **Background Processing**: Celery with Redis broker
- **Browser Automation**: Playwright for SPA-compatible scraping
- **AI Integration**: OpenAI API for natural language configuration generation
