"""
Tests for convention registration endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ulid import ULID

from main import app
from database import get_db, SessionLocal
from models import Users, Attendees, Conventions, Admins

client = TestClient(app)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def override_get_db(db_session):
    """Override the get_db dependency to use test database."""
    def _override():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def sample_data(db_session):
    """Create sample data for testing."""
    # Create admin user
    admin_user = Users(
        id="admin-user-id",
        email="admin@test.com",
        name="Admin User",
        auth_provider="test",
        auth_provider_id="admin123",
        is_active=True
    )
    db_session.add(admin_user)
    
    admin = Admins(
        id=str(ULID()),
        user_id=admin_user.id
    )
    db_session.add(admin)
    
    # Create regular user
    regular_user = Users(
        id="regular-user-id",
        email="user@test.com",
        name="Regular User",
        auth_provider="test",
        auth_provider_id="user123",
        is_active=True
    )
    db_session.add(regular_user)
    
    # Create convention
    convention = Conventions(
        id="test-convention-id",
        name="Test Convention",
        description="Test Description",
        start_date=datetime.now().date(),
        end_date=(datetime.now() + timedelta(days=3)).date(),
        is_active=True
    )
    db_session.add(convention)
    
    db_session.commit()
    
    return {
        "admin_user": admin_user,
        "regular_user": regular_user,
        "convention": convention
    }

def test_register_for_convention_success(override_get_db, sample_data):
    """Test successful convention registration."""
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["regular_user"]
        
        response = client.post(
            f"/conventions/{sample_data['convention'].id}/register",
            json={
                "attendee_id": "regular-user-id"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["convention_id"] == sample_data['convention'].id
        assert data["attendee_name"] == "Regular User"
        assert data["is_registered"] is True

def test_register_for_nonexistent_convention(override_get_db, sample_data):
    """Test registration for non-existent convention."""
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["regular_user"]
        
        response = client.post(
            "/conventions/nonexistent-convention/register",
            json={
                "attendee_id": "regular-user-id"
            }
        )
        
        assert response.status_code == 404
        assert "Convention not found" in response.json()["detail"]

def test_register_with_nonexistent_user(override_get_db, sample_data):
    """Test registration with non-existent user."""
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["regular_user"]
        
        response = client.post(
            f"/conventions/{sample_data['convention'].id}/register",
            json={
                "attendee_id": "nonexistent-user"
            }
        )
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

def test_duplicate_registration(override_get_db, sample_data, db_session):
    """Test duplicate registration for same convention."""
    # Create existing attendee record
    existing_attendee = Attendees(
        id=str(ULID()),
        user_id="regular-user-id",
        convention_id="test-convention-id",
        is_registered=True,
        capability_ids=[]
    )
    db_session.add(existing_attendee)
    db_session.commit()
    
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["regular_user"]
        
        response = client.post(
            f"/conventions/{sample_data['convention'].id}/register",
            json={
                "attendee_id": "regular-user-id"
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

def test_get_my_conventions(override_get_db, sample_data, db_session):
    """Test getting user's registered conventions."""
    # Create attendee record
    attendee = Attendees(
        id=str(ULID()),
        user_id="regular-user-id",
        convention_id="test-convention-id",
        is_registered=True,
        capability_ids=[]
    )
    db_session.add(attendee)
    db_session.commit()
    
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["regular_user"]
        
        response = client.get("/attendees/my-conventions")
        
        assert response.status_code == 200
        data = response.json()
        assert data["attendee_name"] == "Regular User"
        assert len(data["conventions"]) == 1
        assert data["conventions"][0]["id"] == "test-convention-id"
        assert data["conventions"][0]["name"] == "Test Convention"

def test_get_my_conventions_no_registrations(override_get_db, sample_data):
    """Test getting conventions when user has no registrations."""
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["regular_user"]
        
        response = client.get("/attendees/my-conventions")
        
        assert response.status_code == 200
        data = response.json()
        assert data["attendee_name"] == "Regular User"
        assert len(data["conventions"]) == 0

def test_complete_registration_success(override_get_db, sample_data, db_session):
    """Test completing convention registration."""
    # Create pending attendee record
    pending_attendee = Attendees(
        id=str(ULID()),
        user_id="regular-user-id",
        convention_id="test-convention-id",
        is_registered=False,  # Pending registration
        capability_ids=[]
    )
    db_session.add(pending_attendee)
    db_session.commit()
    
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["regular_user"]
        
        response = client.post(
            f"/conventions/{sample_data['convention'].id}/complete-registration",
            json={
                "attendee_id": "regular-user-id",
                "payment_confirmed": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["convention_id"] == sample_data['convention'].id
        assert data["attendee_name"] == "Regular User"
        assert data["is_registered"] is True

def test_complete_registration_no_pending(override_get_db, sample_data):
    """Test completing registration when no pending registration exists."""
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["regular_user"]
        
        response = client.post(
            f"/conventions/{sample_data['convention'].id}/complete-registration",
            json={
                "attendee_id": "regular-user-id",
                "payment_confirmed": True
            }
        )
        
        assert response.status_code == 404
        assert "registration not found" in response.json()["detail"].lower()

def test_admin_list_convention_attendees(override_get_db, sample_data, db_session):
    """Test admin listing all attendees for a convention."""
    # Create multiple attendee records
    attendee1 = Attendees(
        id=str(ULID()),
        user_id="regular-user-id",
        convention_id="test-convention-id",
        is_registered=True,
        capability_ids=[]
    )
    db_session.add(attendee1)
    
    # Create another user and attendee
    user2 = Users(
        id="user2-id",
        email="user2@test.com",
        name="User Two",
        auth_provider="test",
        auth_provider_id="user2123",
        is_active=True
    )
    db_session.add(user2)
    
    attendee2 = Attendees(
        id=str(ULID()),
        user_id="user2-id",
        convention_id="test-convention-id",
        is_registered=True,
        capability_ids=[]
    )
    db_session.add(attendee2)
    db_session.commit()
    
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["admin_user"]
        
        response = client.get(f"/conventions/{sample_data['convention'].id}/attendees")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        attendee_names = [attendee["attendee_name"] for attendee in data]
        assert "Regular User" in attendee_names
        assert "User Two" in attendee_names

def test_non_admin_cannot_list_attendees(override_get_db, sample_data):
    """Test that non-admin users cannot list convention attendees."""
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["regular_user"]
        
        response = client.get(f"/conventions/{sample_data['convention'].id}/attendees")
        
        assert response.status_code == 403

def test_get_convention_schedule(override_get_db, sample_data):
    """Test getting convention schedule."""
    response = client.get(f"/conventions/{sample_data['convention'].id}/schedule")
    
    assert response.status_code == 200
    data = response.json()
    assert data["convention_id"] == sample_data['convention'].id
    assert data["convention_name"] == "Test Convention"
    assert "schedule" in data
    # Empty schedule since no slots/workshops created yet
    assert data["schedule"] == {}

def test_get_schedule_nonexistent_convention(override_get_db, sample_data):
    """Test getting schedule for non-existent convention."""
    response = client.get("/conventions/nonexistent-convention/schedule")
    
    assert response.status_code == 404
    assert "Convention not found" in response.json()["detail"]

def test_unauthorized_complete_registration(override_get_db, sample_data):
    """Test that unauthenticated users cannot complete registration."""
    response = client.post(
        f"/conventions/{sample_data['convention'].id}/complete-registration",
        json={
            "attendee_id": "regular-user-id",
            "payment_confirmed": True
        }
    )
    
    # Should require authentication
    assert response.status_code in [401, 403]