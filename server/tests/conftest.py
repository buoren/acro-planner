"""
Pytest configuration and fixtures for Acro Planner tests.

This module provides shared fixtures for database sessions, test clients,
authentication, and test data.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import ulid  # type: ignore  # ulid-py package

# Import before creating test database to register models
from database import Base, get_db
from models import Users
from utils.auth import create_password_hash
from main import app


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
    return user


@pytest.fixture
def test_user_host(db_session):
    """
    Create a test user with 'host' role.
    Note: role and is_approved_host fields will be added in Phase 1.
    For now, this creates a regular user that will be upgraded in Phase 1 tests.
    """
    user_id = str(ulid.new())
    password_hash, salt = create_password_hash("testpassword123")
    
    # TODO: Add role="host" and is_approved_host=True when Phase 1 is implemented
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
    return user


@pytest.fixture
def test_user_admin(db_session):
    """
    Create a test user with 'admin' role.
    Note: role and is_approved_host fields will be added in Phase 1.
    For now, this creates a regular user that will be upgraded in Phase 1 tests.
    """
    user_id = str(ulid.new())
    password_hash, salt = create_password_hash("testpassword123")
    
    # TODO: Add role="admin" and is_approved_host=True when Phase 1 is implemented
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
    return user


def create_auth_override(user, db_session):
    """Helper to create authentication override for a user."""
    from oauth import get_current_user
    from models import Users
    
    # Fetch user from database to ensure we have latest data (including role if it exists)
    db_user = db_session.query(Users).filter(Users.id == user.id).first()
    
    user_dict = {
        'email': db_user.email,
        'name': db_user.name,
        'sub': db_user.id,
        'auth_method': 'test'
    }
    
    # Add role if it exists (will be available after Phase 1)
    if hasattr(db_user, 'role'):
        user_dict['role'] = db_user.role
    
    def mock_get_current_user(request):
        return user_dict
    
    return mock_get_current_user


@pytest.fixture
def authenticated_client_attendee(test_client, test_user_attendee, db_session):
    """Test client authenticated as attendee user."""
    from oauth import get_current_user
    
    mock_func = create_auth_override(test_user_attendee, db_session)
    app.dependency_overrides[get_current_user] = mock_func
    
    yield test_client
    
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]


@pytest.fixture
def authenticated_client_host(test_client, test_user_host, db_session):
    """Test client authenticated as host user."""
    from oauth import get_current_user
    
    mock_func = create_auth_override(test_user_host, db_session)
    app.dependency_overrides[get_current_user] = mock_func
    
    yield test_client
    
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]


@pytest.fixture
def authenticated_client_admin(test_client, test_user_admin, db_session):
    """Test client authenticated as admin user."""
    from oauth import get_current_user
    
    mock_func = create_auth_override(test_user_admin, db_session)
    app.dependency_overrides[get_current_user] = mock_func
    
    yield test_client
    
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]


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

