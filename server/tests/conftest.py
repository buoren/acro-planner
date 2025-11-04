"""
Pytest configuration and fixtures for Acro Planner tests.

This module provides shared fixtures for database sessions, test clients,
authentication, and test data.
"""

import pytest
import ulid  # type: ignore  # ulid-py package
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import before creating test database to register models
from database import Base, get_db
from main import app
from models import Users, Attendees, Hosts, Admins
from utils.auth import create_password_hash
from utils.roles import add_attendee_role, add_host_role, add_admin_role

# Test database configuration - use SQLite in-memory for speed
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Create a fresh database session for each test.
    Creates tables, yields session, then drops tables.
    """
    # Create tables
    Base.metadata.create_all(bind=test_engine)

    # Create session
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        # Drop tables
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def test_client(db_session):
    """
    Create a test client with database override.
    Overrides the get_db dependency to use test database.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_attendee(db_session):
    """Create a test user with 'attendee' role."""
    user_id = str(ulid.new())
    password_hash, salt = create_password_hash("testpassword123")

    user = Users(
        id=user_id,
        email="attendee@test.com",
        name="Test Attendee",
        password_hash=password_hash,
        salt=salt
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Add attendee role
    add_attendee_role(db_session, user_id)
    
    return user


@pytest.fixture
def test_user_host(db_session):
    """Create a test user with 'host' and 'attendee' roles."""
    user_id = str(ulid.new())
    password_hash, salt = create_password_hash("testpassword123")

    user = Users(
        id=user_id,
        email="host@test.com",
        name="Test Host",
        password_hash=password_hash,
        salt=salt
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Add attendee role first (hosts must be attendees)
    attendee = add_attendee_role(db_session, user_id)
    # Then add host role
    add_host_role(db_session, user_id, attendee.id)
    
    return user


@pytest.fixture
def test_user_admin(db_session):
    """Create a test user with 'admin' role."""
    user_id = str(ulid.new())
    password_hash, salt = create_password_hash("testpassword123")

    user = Users(
        id=user_id,
        email="admin@test.com",
        name="Test Admin",
        password_hash=password_hash,
        salt=salt
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Add admin role
    add_admin_role(db_session, user_id)
    
    return user


def create_auth_override(user, db_session):
    """Helper to create authentication override for a user."""
    from models import Users
    from oauth import get_current_user
    from utils.roles import get_user_with_roles

    # Get user with role information
    user_with_roles = get_user_with_roles(db_session, user.id)
    
    if user_with_roles:
        user_dict = {
            'email': user_with_roles['email'],
            'name': user_with_roles['name'],
            'sub': user_with_roles['id'],
            'id': user_with_roles['id'],
            'roles': user_with_roles['roles'],
            'is_admin': user_with_roles['is_admin'],
            'is_host': user_with_roles['is_host'],
            'is_attendee': user_with_roles['is_attendee'],
            'auth_method': 'test'
        }
    else:
        # Fallback if role lookup fails
        user_dict = {
            'email': user.email,
            'name': user.name,
            'sub': user.id,
            'id': user.id,
            'roles': [],
            'is_admin': False,
            'is_host': False,
            'is_attendee': False,
            'auth_method': 'test'
        }

    def mock_get_current_user(request):
        return user_dict

    return mock_get_current_user


@pytest.fixture
def authenticated_client_attendee(test_client, test_user_attendee, db_session):
    """Test client authenticated as attendee user."""
    from oauth import get_current_user
    from api.auth import require_auth

    mock_func = create_auth_override(test_user_attendee, db_session)
    
    # Mock both the oauth function and the auth dependency
    app.dependency_overrides[get_current_user] = mock_func
    app.dependency_overrides[require_auth] = lambda: mock_func(None)  # Return user dict directly

    yield test_client

    # Clean up
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]
    if require_auth in app.dependency_overrides:
        del app.dependency_overrides[require_auth]


@pytest.fixture
def authenticated_client_host(test_client, test_user_host, db_session):
    """Test client authenticated as host user."""
    from oauth import get_current_user
    from api.auth import require_auth

    mock_func = create_auth_override(test_user_host, db_session)
    
    app.dependency_overrides[get_current_user] = mock_func
    app.dependency_overrides[require_auth] = lambda: mock_func(None)

    yield test_client

    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]
    if require_auth in app.dependency_overrides:
        del app.dependency_overrides[require_auth]


@pytest.fixture
def authenticated_client_admin(test_client, test_user_admin, db_session):
    """Test client authenticated as admin user."""
    from oauth import get_current_user
    from api.auth import require_auth

    mock_func = create_auth_override(test_user_admin, db_session)
    
    app.dependency_overrides[get_current_user] = mock_func
    app.dependency_overrides[require_auth] = lambda: mock_func(None)

    yield test_client

    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]
    if require_auth in app.dependency_overrides:
        del app.dependency_overrides[require_auth]


@pytest.fixture
def unauthenticated_client(test_client):
    """Test client without authentication."""
    from oauth import get_current_user

    def mock_get_current_user(request):
        return None

    app.dependency_overrides[get_current_user] = mock_get_current_user

    yield test_client

    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]

