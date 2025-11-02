# Acro Planner Test Framework

This directory contains tests for the Acro Planner API using pytest and FastAPI's TestClient.

## Setup

Install test dependencies:

```bash
# Using Poetry (recommended)
cd server
poetry install --with dev

# Or using pip
pip install pytest pytest-asyncio pytest-cov httpx mypy ruff types-requests
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov

# Run specific test file
pytest tests/test_example.py

# Run tests matching a pattern
pytest -k "test_user"

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run tests with verbose output
pytest -v
```

## Test Structure

### Fixtures

The `conftest.py` file provides the following fixtures:

#### Database Fixtures
- `db_session`: Fresh database session for each test (SQLite in-memory)
- `test_client`: FastAPI TestClient with database override

#### User Fixtures
- `test_user_attendee`: Creates a test user with attendee role (after Phase 1)
- `test_user_host`: Creates a test user with host role (after Phase 1)
- `test_user_admin`: Creates a test user with admin role (after Phase 1)

#### Authentication Fixtures
- `authenticated_client_attendee`: Test client authenticated as attendee
- `authenticated_client_host`: Test client authenticated as host
- `authenticated_client_admin`: Test client authenticated as admin
- `unauthenticated_client`: Test client without authentication

## Writing Tests

### Example Test

```python
import pytest
from fastapi import status

@pytest.mark.integration
def test_get_users(test_client, db_session):
    """Test getting list of users."""
    response = test_client.get("/users/")
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.integration
@pytest.mark.auth
def test_create_user_requires_auth(unauthenticated_client):
    """Test that creating user requires authentication."""
    response = unauthenticated_client.post("/users/register", json={...})
    # Should fail without auth
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
```

### Test Markers

Use markers to categorize tests:

- `@pytest.mark.unit`: Unit tests for individual functions
- `@pytest.mark.integration`: Integration tests for API endpoints
- `@pytest.mark.auth`: Tests related to authentication/authorization
- `@pytest.mark.slow`: Tests that take a long time

## Test Database

Tests use an in-memory SQLite database that is:
- Created fresh for each test
- Automatically cleaned up after each test
- Isolated from the production database

## Test-Driven Development (TDD)

Following the implementation plan, all tests for a phase must be written BEFORE implementing that phase's endpoints.

### Phase 1 Example:
1. Write all tests in `tests/test_user_roles.py`
2. Run tests (they will fail - expected)
3. Implement Phase 1 endpoints
4. Run tests again (they should pass)
5. Move to Phase 2

## Coverage

Test coverage is automatically generated and can be viewed:

```bash
# Generate HTML coverage report
pytest --cov --cov-report=html

# Open coverage report
open htmlcov/index.html
```

## Code Quality Checks

The project uses ruff for linting and mypy for type checking.

### Linting (ruff)

```bash
# Check for linting issues
make lint
# or
poetry run ruff check .

# Auto-fix linting issues
make lint-fix
# or
poetry run ruff check --fix .
```

### Type Checking (mypy)

```bash
# Run type checker
make type-check
# or
poetry run mypy .
```

### Run All Checks

```bash
# Run lint, type-check, and tests
make check
```

## Makefile Commands

The project includes a Makefile for common tasks:

```bash
make help          # Show all available commands
make install-dev   # Install all dependencies including dev
make test          # Run tests
make test-cov      # Run tests with coverage
make lint          # Run ruff linter
make lint-fix      # Run ruff and fix issues
make type-check    # Run mypy type checker
make check         # Run all checks (lint, type-check, tests)
make format        # Format code with ruff
make clean         # Clean up generated files
```

## CI/CD Integration

### Cloud Build (Google Cloud)

The `cloudbuild.yaml` file automatically runs:
1. Ruff linter
2. MyPy type checker
3. Pytest tests with coverage

All checks must pass before building the Docker image.

### GitHub Actions

If using GitHub Actions, see `.github/workflows/ci.yml` for the CI workflow.

## Notes

- Tests are isolated and can run in any order
- Each test gets a fresh database session
- Authentication is mocked using FastAPI dependency overrides
- Test database uses SQLite for speed (production uses MySQL)
- All code must pass ruff linting and mypy type checking before deployment

