# Authentication App Tests

This directory contains comprehensive unit tests for the authentication app's User model and related functionality.

## Test Structure

### Test Files

- **`test_models.py`** - Core User model functionality tests
  - User creation and validation
  - Field constraints and behavior
  - Model methods and properties
  - Authentication integration

- **`test_user_integration.py`** - Integration tests with Django components
  - Authentication system integration
  - Database transaction handling
  - Admin interface integration
  - Django signals integration
  - Migration testing

- **`test_user_edge_cases.py`** - Edge cases and performance tests
  - Boundary value testing
  - Unicode and special character handling
  - Concurrency and race condition testing
  - Performance benchmarks
  - Bulk operations testing

- **`test_settings.py`** - Test utilities and configuration
  - Base test case classes
  - Helper methods for test data creation
  - Test constants and settings

- **`test_runner.py`** - Custom test runner and discovery
  - Enhanced test environment setup
  - Test suite organization
  - Batch test execution utilities

## Running Tests

### Using Django's Test Command

```bash
# Run all authentication tests
python manage.py test apps.authentication.tests

# Run specific test file
python manage.py test apps.authentication.tests.test_models

# Run specific test class
python manage.py test apps.authentication.tests.test_models.UserModelTest

# Run specific test method
python manage.py test apps.authentication.tests.test_models.UserModelTest.test_create_user_with_email

# Run with higher verbosity
python manage.py test apps.authentication.tests --verbosity=2

# Stop on first failure
python manage.py test apps.authentication.tests --failfast
```

### Using Custom Management Command

```bash
# Run all authentication tests with custom runner
python manage.py test_auth

# Run specific module
python manage.py test_auth --module=test_models

# Run with failfast
python manage.py test_auth --failfast

# Run with specific verbosity
python manage.py test_auth --verbosity=1
```

### Using Docker

```bash
# Run tests in Docker container
docker-compose exec web python manage.py test apps.authentication.tests

# Run with coverage
docker-compose exec web coverage run --source='.' manage.py test apps.authentication.tests
docker-compose exec web coverage report
```

## Test Categories

### Unit Tests
- Test individual User model methods
- Validate field constraints and behavior
- Test model validation logic
- Verify string representations and meta options

### Integration Tests
- Test User model with Django's authentication system
- Verify database transaction handling
- Test admin interface integration
- Validate signal handling

### Edge Case Tests
- Test boundary conditions (max length fields, etc.)
- Unicode and internationalization support
- Concurrent access scenarios
- Performance under load

### Performance Tests
- Bulk user creation and updates
- Query performance with large datasets
- Authentication performance benchmarks
- Concurrent operation handling

## Test Data

### Default Test User Data
```python
{
    'email': 'test@example.com',
    'username': 'testuser',
    'password': 'testpass123',
    'first_name': 'Test',
    'last_name': 'User'
}
```

### Test Utilities

The `test_settings.py` file provides several utility functions:

- `create_test_user(**kwargs)` - Create test user with default or custom data
- `create_test_superuser(**kwargs)` - Create test superuser
- `assertUserFieldsEqual(user, expected_data)` - Assert user fields match expected values
- `assertUserExists(**lookup_kwargs)` - Assert user exists with criteria
- `create_test_users_batch(count, prefix)` - Create multiple test users

## Coverage Goals

These tests aim to achieve:
- **95%+ code coverage** for User model and related code
- **100% coverage** of critical authentication paths
- **Edge case coverage** for all field validations
- **Performance benchmarks** for scalability testing

## Test Database

Tests use an in-memory SQLite database by default for speed. For more realistic testing, you can configure PostgreSQL:

```python
# In test settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'test_watcher',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## Continuous Integration

These tests are designed to run in CI environments:

```yaml
# Example GitHub Actions workflow
- name: Run Authentication Tests
  run: |
    python manage.py test apps.authentication.tests --verbosity=2
    
- name: Run Tests with Coverage
  run: |
    coverage run --source='.' manage.py test apps.authentication.tests
    coverage xml
```

## Performance Benchmarks

Current performance thresholds:
- User creation: < 30 seconds for 1000 users
- Complex queries: < 5 seconds
- Bulk updates: < 2 seconds for 1000 users
- Authentication: < 5 seconds for 100 attempts

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure Django is properly configured and apps are installed
2. **Database Errors**: Check database permissions and connection settings
3. **Migration Issues**: Run `python manage.py migrate` before tests
4. **Performance Issues**: Consider using PostgreSQL for more realistic performance testing

### Debug Mode

Run tests with debug output:
```bash
python manage.py test apps.authentication.tests --debug-mode --verbosity=3
```

### Test Isolation

Each test method runs in a transaction that's rolled back after completion, ensuring test isolation. For tests that need to test transaction behavior specifically, use `TransactionTestCase`.

## Contributing

When adding new tests:
1. Follow the existing naming conventions
2. Add docstrings explaining test purpose
3. Use appropriate test base classes
4. Include both positive and negative test cases
5. Add performance tests for new functionality
6. Update this README if adding new test categories