# Project Structure

## Root Directory Layout
```
watcher/
├── docker-compose.yml          # Multi-service orchestration
├── .env                        # Environment variables
├── .dockerignore              # Docker build exclusions
├── README.md                  # Project documentation
├── backend/                   # Django application
├── frontend/                  # React application
└── .kiro/                     # Kiro configuration and specs
```

## Backend Structure (Django)
```
backend/
├── Dockerfile                 # Django container definition
├── requirements.txt           # Python dependencies
├── manage.py                  # Django management script
├── watcher/                   # Main Django project
│   ├── __init__.py
│   ├── settings/              # Environment-specific settings
│   │   ├── __init__.py
│   │   ├── base.py           # Common settings
│   │   ├── development.py    # Dev-specific settings
│   │   └── production.py     # Prod-specific settings
│   ├── urls.py               # Root URL configuration
│   ├── wsgi.py               # WSGI application
│   └── celery.py             # Celery configuration
├── apps/                     # Django applications
│   ├── authentication/       # User auth and JWT
│   ├── haunts/              # Core haunt management
│   ├── scraping/            # Playwright scraping service
│   ├── rss/                 # RSS feed generation
│   ├── ai/                  # LLM integration service
│   └── subscriptions/       # Public haunt subscriptions
└── tests/                   # Test modules
    ├── fixtures/            # Test data
    ├── integration/         # Integration tests
    └── unit/               # Unit tests
```

## Frontend Structure (React)
```
frontend/
├── Dockerfile               # React container definition
├── package.json            # Node.js dependencies
├── tsconfig.json           # TypeScript configuration
├── public/                 # Static assets
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── common/        # Generic components
│   │   ├── navigation/    # Left panel components
│   │   ├── itemList/      # Middle panel components
│   │   └── itemDetail/    # Right panel components
│   ├── pages/             # Route-level components
│   ├── store/             # Redux store configuration
│   │   ├── slices/        # Redux Toolkit slices
│   │   └── api.ts         # API client configuration
│   ├── services/          # Business logic services
│   ├── hooks/             # Custom React hooks
│   ├── utils/             # Utility functions
│   └── types/             # TypeScript type definitions
└── tests/                 # Frontend tests
```

## Django App Organization

### Core Apps Structure
Each Django app follows this pattern:
```
apps/[app_name]/
├── __init__.py
├── models.py              # Database models
├── serializers.py         # DRF serializers
├── views.py               # API viewsets
├── urls.py                # App-specific URLs
├── services.py            # Business logic
├── tasks.py               # Celery tasks (if applicable)
├── admin.py               # Django admin configuration
├── migrations/            # Database migrations
└── tests/                 # App-specific tests
```

### Key Model Relationships
- **User** → owns → **Haunt** (one-to-many)
- **Haunt** → belongs to → **Folder** (many-to-one, optional)
- **Haunt** → generates → **RSSItem** (one-to-many)
- **User** → subscribes to → **Haunt** (many-to-many via Subscription)
- **User** → tracks → **RSSItem** (many-to-many via UserReadState)

## Configuration Management

### Environment Variables
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection for Celery
- `LLM_API_KEY` - AI service authentication
- `SECRET_KEY` - Django secret key
- `DEBUG` - Development mode flag
- `ALLOWED_HOSTS` - Django allowed hosts

### Docker Services
- `web` - Django API server (port 8000)
- `frontend` - React dev server (port 3000) or Nginx (port 80)
- `db` - PostgreSQL database (port 5432)
- `redis` - Redis server (port 6379)
- `celery` - Background worker processes
- `scheduler` - Celery beat scheduler

## API Endpoint Organization
```
/api/v1/
├── auth/                  # Authentication endpoints
├── haunts/                # Haunt CRUD operations
├── folders/               # Folder management
├── subscriptions/         # Public haunt subscriptions
├── rss/                   # RSS feed endpoints
└── user/                  # User preferences and settings
```

## File Naming Conventions

### Backend (Python)
- **Models**: PascalCase classes (`class Haunt(models.Model)`)
- **Files**: snake_case (`haunt_service.py`, `rss_generator.py`)
- **Functions**: snake_case (`generate_config()`, `scrape_haunt()`)
- **Constants**: UPPER_SNAKE_CASE (`SCRAPE_INTERVALS`, `ALERT_MODES`)

### Frontend (TypeScript/React)
- **Components**: PascalCase (`NavigationPanel.tsx`, `ItemDetail.tsx`)
- **Files**: camelCase for utilities (`apiClient.ts`, `keyboardShortcuts.ts`)
- **Interfaces**: PascalCase with descriptive names (`HauntConfig`, `RSSItem`)
- **Hooks**: camelCase starting with 'use' (`useHaunts`, `useKeyboardShortcuts`)

## Testing Organization
- **Unit tests**: Test individual functions and components in isolation
- **Integration tests**: Test API endpoints with database interactions
- **E2E tests**: Test complete user workflows with browser automation
- **Performance tests**: Test scraping concurrency and database performance