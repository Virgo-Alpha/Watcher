# Contributing to Watcher

Thanks for your interest in contributing to Watcher! This guide will help you get started.

## Code of Conduct

Be respectful, inclusive, and constructive. We're building a tool to help people monitor the web efficiently.

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Git
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/watcher.git
   cd watcher
   ```

2. **Copy environment variables**
   ```bash
   cp .env.example .env
   ```

3. **Start development environment**
   ```bash
   docker-compose up -d
   ```

4. **Run migrations**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

5. **Create a superuser**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

6. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Django Admin: http://localhost:8000/admin

## How to Contribute

### Reporting Bugs

Open a GitHub issue with:
- Clear, descriptive title
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Docker version, etc.)
- Screenshots if applicable

### Suggesting Features

Open a GitHub issue with:
- Clear description of the feature
- Use case and benefits
- Potential implementation approach
- Mockups or examples if applicable

### Submitting Pull Requests

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow existing code style
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   # Backend tests
   docker-compose exec web python manage.py test
   
   # Frontend tests
   docker-compose exec frontend npm test
   ```

4. **Commit with clear messages**
   ```bash
   git commit -m "feat: add natural language haunt configuration"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **PR Guidelines**
   - Reference related issues
   - Describe what changed and why
   - Include screenshots for UI changes
   - Ensure CI passes

## Development Guidelines

### Code Style

#### Python (Backend)
- Follow PEP 8
- Use type hints where appropriate
- Maximum line length: 100 characters
- Use Django conventions
- Run `black` and `flake8` before committing

```bash
# Format code
docker-compose exec web black .

# Check linting
docker-compose exec web flake8
```

#### TypeScript/React (Frontend)
- Use functional components with hooks
- Follow Airbnb style guide
- Use TypeScript for type safety
- Prefer named exports
- Run ESLint and Prettier

```bash
# Format code
docker-compose exec frontend npm run format

# Check linting
docker-compose exec frontend npm run lint
```

### Commit Messages

Follow conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Examples:
```
feat: add keyboard shortcuts for navigation
fix: resolve RSS feed generation for empty haunts
docs: update API endpoint documentation
refactor: simplify haunt configuration validation
```

### Testing

#### Backend Tests
```bash
# Run all tests
docker-compose exec web python manage.py test

# Run specific app tests
docker-compose exec web python manage.py test apps.haunts

# Run with coverage
docker-compose exec web coverage run --source='.' manage.py test
docker-compose exec web coverage report
```

#### Frontend Tests
```bash
# Run all tests
docker-compose exec frontend npm test

# Run with coverage
docker-compose exec frontend npm test -- --coverage

# Run specific test file
docker-compose exec frontend npm test -- ItemList.test.tsx
```

### Database Migrations

When modifying models:

```bash
# Create migration
docker-compose exec web python manage.py makemigrations

# Review migration file
# Edit if needed for data migrations

# Apply migration
docker-compose exec web python manage.py migrate

# Test rollback
docker-compose exec web python manage.py migrate app_name previous_migration
```

### Adding Dependencies

#### Python
1. Add to `backend/requirements.txt`
2. Rebuild container: `docker-compose build web`
3. Document why the dependency is needed

#### Node.js
1. Add via npm: `docker-compose exec frontend npm install package-name`
2. Commit updated `package.json` and `package-lock.json`
3. Document why the dependency is needed

## Project Areas

### Backend (Django)

**Key areas for contribution:**
- `apps/haunts/` - Core haunt management
- `apps/scraping/` - Playwright scraping service
- `apps/ai/` - AI configuration generation
- `apps/rss/` - RSS feed generation
- `apps/authentication/` - User auth and JWT

### Frontend (React)

**Key areas for contribution:**
- `src/components/navigation/` - Left sidebar
- `src/components/itemList/` - Middle panel (feed list)
- `src/components/itemDetail/` - Right panel (content view)
- `src/store/` - Redux state management
- `src/services/` - API integration

### Infrastructure

**Key areas for contribution:**
- Docker configuration
- Celery task optimization
- Database performance
- Caching strategies
- Deployment documentation

## Feature Development Workflow

1. **Discuss first** - Open an issue to discuss major features
2. **Design** - Create technical design doc if needed
3. **Implement** - Build feature with tests
4. **Document** - Update relevant docs
5. **Review** - Submit PR for review
6. **Iterate** - Address feedback
7. **Merge** - Maintainer merges when ready

## Documentation

Update documentation when:
- Adding new features
- Changing APIs
- Modifying configuration
- Adding dependencies
- Changing deployment process

Documentation locations:
- `README.md` - Project overview
- `USER_GUIDE.md` - User-facing features
- `MCP_SETUP_GUIDE.md` - MCP integration
- `QUICK_START.md` - Getting started
- `.kiro/steering/` - Development guidelines

## Review Process

PRs are reviewed for:
- Code quality and style
- Test coverage
- Documentation updates
- Breaking changes
- Performance impact
- Security considerations

Expect feedback within 3-5 days. Be patient and responsive to reviewer comments.

## Release Process

Maintainers handle releases:
1. Version bump (semantic versioning)
2. Update CHANGELOG.md
3. Create GitHub release
4. Deploy to production
5. Announce in discussions

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue
- **Security**: See SECURITY.md
- **Chat**: [Add Discord/Slack link if available]

## Recognition

Contributors are recognized in:
- GitHub contributors page
- Release notes
- Project README

Thank you for contributing to Watcher! 🎉
