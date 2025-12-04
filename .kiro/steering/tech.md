# Technology Stack

## Architecture
- **Containerized microservices** using Docker Compose
- **Backend**: Django REST Framework with PostgreSQL database
- **Frontend**: React with Redux for state management
- **Background Processing**: Celery with Redis broker
- **Browser Automation**: Playwright for SPA-compatible scraping
- **AI Integration**: OpenAI API for natural language configuration generation

## Core Technologies

### Backend Stack
- **Django 4.x** with Django REST Framework
- **PostgreSQL** for primary data storage
- **Redis** for Celery message broker and caching
- **Celery** for background task processing and scheduling
- **Playwright** for headless browser automation
- **JWT** for authentication

### Frontend Stack
- **React 18+** with functional components and hooks
- **Redux Toolkit** for state management
- **TypeScript** for type safety
- **CSS Modules** or styled-components for styling

### Infrastructure
- **Docker & Docker Compose** for containerization
- **Nginx** for production static file serving
- **Environment-based configuration** for dev/staging/prod

### AI Integration
- **OpenAI GPT-3.5-turbo** for converting natural language descriptions to CSS selectors
- **Configuration validation** with JSON schema validation
- **Fallback summaries** when AI service is unavailable
- **Rate limiting** and error handling for API calls

## Common Commands

### Development Setup
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f [service_name]

# Run Django migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Test AI service configuration
docker-compose exec web python manage.py shell -c "from apps.ai.services import AIConfigService; print('AI Available:', AIConfigService().is_available())"

# Run tests
docker-compose exec web python manage.py test
```

### Frontend Development
```bash
# Install dependencies
docker-compose exec frontend npm install

# Start development server (if not using Docker)
npm start

# Run frontend tests
docker-compose exec frontend npm test

# Build for production
docker-compose exec frontend npm run build
```

### Background Tasks
```bash
# Monitor Celery workers
docker-compose exec celery celery -A watcher worker --loglevel=info

# Monitor scheduled tasks
docker-compose exec scheduler celery -A watcher beat --loglevel=info

# Inspect active tasks
docker-compose exec celery celery -A watcher inspect active
```

### Database Operations
```bash
# Access PostgreSQL shell
docker-compose exec db psql -U postgres -d watcher

# Create migration
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate

# Load fixtures
docker-compose exec web python manage.py loaddata fixtures/sample_data.json
```

## Key Dependencies

### Python (requirements.txt)
- `django>=4.2`
- `djangorestframework>=3.14`
- `celery>=5.3`
- `redis>=4.5`
- `playwright>=1.40`
- `psycopg2-binary>=2.9`
- `djangorestframework-simplejwt>=5.3`
- `openai>=1.3` - OpenAI API client for AI-powered configuration generation

### Node.js (package.json)
- `react>=18.0`
- `@reduxjs/toolkit>=1.9`
- `typescript>=4.9`
- `@types/react>=18.0`