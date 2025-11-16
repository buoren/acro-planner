"""
Tests for bulk slot creation endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ulid import ULID

from main import app
from database import get_db, SessionLocal
from models import Users, Admins, Conventions, Locations, EventSlot

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
    
    # Create regular user (non-admin)
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
    
    # Create locations
    location1 = Locations(
        id="location-1",
        name="Main Hall",
        convention_id="test-convention-id",
        description="Main presentation hall",
        capacity=100,
        address="123 Convention Center",
        equipment_ids=[]
    )
    db_session.add(location1)
    
    location2 = Locations(
        id="location-2",
        name="Workshop Room A",
        convention_id="test-convention-id",
        description="Smaller workshop room",
        capacity=25,
        address="123 Convention Center, Room A",
        equipment_ids=[]
    )
    db_session.add(location2)
    
    db_session.commit()
    
    return {
        "admin_user": admin_user,
        "regular_user": regular_user,
        "convention": convention,
        "location1": location1,
        "location2": location2
    }

def test_create_bulk_slots_success(override_get_db, sample_data, db_session):
    """Test successful bulk slot creation."""
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["admin_user"]
        
        request_data = {
            "convention_id": "test-convention-id",
            "location_ids": ["location-1", "location-2"],
            "time_slots": [
                {"start_time": "09:00", "end_time": "10:30"},
                {"start_time": "11:00", "end_time": "12:30"},
                {"start_time": "14:00", "end_time": "15:30"}
            ],
            "number_of_days": 2
        }
        
        response = client.post(
            f"/conventions/test-convention-id/bulk-slots",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["convention_id"] == "test-convention-id"
        # 3 time slots * 2 locations * 2 days = 12 slots
        assert data["total_slots_created"] == 12
        assert len(data["slots"]) == 12
        
        # Verify slots were actually created in database
        created_slots = db_session.query(EventSlot).filter(
            EventSlot.convention_id == "test-convention-id"
        ).count()
        assert created_slots == 12

def test_create_bulk_slots_single_location(override_get_db, sample_data, db_session):
    """Test bulk slot creation with single location."""
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["admin_user"]
        
        request_data = {
            "convention_id": "test-convention-id",
            "location_ids": ["location-1"],
            "time_slots": [
                {"start_time": "09:00", "end_time": "10:30"},
                {"start_time": "11:00", "end_time": "12:30"}
            ],
            "number_of_days": 1
        }
        
        response = client.post(
            f"/conventions/test-convention-id/bulk-slots",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        # 2 time slots * 1 location * 1 day = 2 slots
        assert data["total_slots_created"] == 2

def test_create_bulk_slots_invalid_time_format(override_get_db, sample_data):
    """Test bulk slot creation with invalid time format."""
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["admin_user"]
        
        request_data = {
            "convention_id": "test-convention-id",
            "location_ids": ["location-1"],
            "time_slots": [
                {"start_time": "9:00", "end_time": "10:30"},  # Should be 09:00
            ],
            "number_of_days": 1
        }
        
        response = client.post(
            f"/conventions/test-convention-id/bulk-slots",
            json=request_data
        )
        
        assert response.status_code == 422  # Validation error

def test_create_bulk_slots_end_before_start(override_get_db, sample_data):
    """Test bulk slot creation with end time before start time."""
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["admin_user"]
        
        request_data = {
            "convention_id": "test-convention-id",
            "location_ids": ["location-1"],
            "time_slots": [
                {"start_time": "12:00", "end_time": "11:00"},  # End before start
            ],
            "number_of_days": 1
        }
        
        response = client.post(
            f"/conventions/test-convention-id/bulk-slots",
            json=request_data
        )
        
        assert response.status_code == 400
        assert "must be after start time" in response.json()["detail"]

def test_create_bulk_slots_too_many_days(override_get_db, sample_data):
    """Test bulk slot creation with too many days."""
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["admin_user"]
        
        request_data = {
            "convention_id": "test-convention-id",
            "location_ids": ["location-1"],
            "time_slots": [
                {"start_time": "09:00", "end_time": "10:30"}
            ],
            "number_of_days": 31  # More than 30 allowed
        }
        
        response = client.post(
            f"/conventions/test-convention-id/bulk-slots",
            json=request_data
        )
        
        assert response.status_code == 422  # Validation error

def test_create_bulk_slots_too_many_time_slots(override_get_db, sample_data):
    """Test bulk slot creation with too many time slots."""
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["admin_user"]
        
        # Create 21 time slots (more than 20 allowed)
        time_slots = []
        for i in range(21):
            start_hour = 8 + i
            end_hour = start_hour + 1
            time_slots.append({
                "start_time": f"{start_hour:02d}:00",
                "end_time": f"{end_hour:02d}:00"
            })
        
        request_data = {
            "convention_id": "test-convention-id",
            "location_ids": ["location-1"],
            "time_slots": time_slots,
            "number_of_days": 1
        }
        
        response = client.post(
            f"/conventions/test-convention-id/bulk-slots",
            json=request_data
        )
        
        assert response.status_code == 422  # Validation error

def test_create_bulk_slots_nonexistent_convention(override_get_db, sample_data):
    """Test bulk slot creation for non-existent convention."""
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["admin_user"]
        
        request_data = {
            "convention_id": "nonexistent-convention",
            "location_ids": ["location-1"],
            "time_slots": [
                {"start_time": "09:00", "end_time": "10:30"}
            ],
            "number_of_days": 1
        }
        
        response = client.post(
            "/conventions/nonexistent-convention/bulk-slots",
            json=request_data
        )
        
        assert response.status_code == 404
        assert "Convention not found" in response.json()["detail"]

def test_create_bulk_slots_nonexistent_location(override_get_db, sample_data):
    """Test bulk slot creation with non-existent location."""
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["admin_user"]
        
        request_data = {
            "convention_id": "test-convention-id",
            "location_ids": ["location-1", "nonexistent-location"],
            "time_slots": [
                {"start_time": "09:00", "end_time": "10:30"}
            ],
            "number_of_days": 1
        }
        
        response = client.post(
            f"/conventions/test-convention-id/bulk-slots",
            json=request_data
        )
        
        assert response.status_code == 404
        assert "not found in this convention" in response.json()["detail"]

def test_create_bulk_slots_location_from_different_convention(override_get_db, sample_data, db_session):
    """Test bulk slot creation with location from different convention."""
    # Create another convention
    other_convention = Conventions(
        id="other-convention-id",
        name="Other Convention",
        description="Other Description",
        start_date=datetime.now().date(),
        end_date=(datetime.now() + timedelta(days=3)).date(),
        is_active=True
    )
    db_session.add(other_convention)
    
    # Create location for other convention
    other_location = Locations(
        id="other-location",
        name="Other Location",
        convention_id="other-convention-id",
        description="Location for other convention",
        capacity=50,
        address="456 Other St",
        equipment_ids=[]
    )
    db_session.add(other_location)
    db_session.commit()
    
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["admin_user"]
        
        request_data = {
            "convention_id": "test-convention-id",
            "location_ids": ["other-location"],  # Location from different convention
            "time_slots": [
                {"start_time": "09:00", "end_time": "10:30"}
            ],
            "number_of_days": 1
        }
        
        response = client.post(
            f"/conventions/test-convention-id/bulk-slots",
            json=request_data
        )
        
        assert response.status_code == 404
        assert "not found in this convention" in response.json()["detail"]

def test_create_bulk_slots_unauthorized(override_get_db, sample_data):
    """Test that non-admin users cannot create bulk slots."""
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["regular_user"]
        
        request_data = {
            "convention_id": "test-convention-id",
            "location_ids": ["location-1"],
            "time_slots": [
                {"start_time": "09:00", "end_time": "10:30"}
            ],
            "number_of_days": 1
        }
        
        response = client.post(
            f"/conventions/test-convention-id/bulk-slots",
            json=request_data
        )
        
        assert response.status_code == 403

def test_create_bulk_slots_no_time_slots(override_get_db, sample_data):
    """Test bulk slot creation with no time slots."""
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["admin_user"]
        
        request_data = {
            "convention_id": "test-convention-id",
            "location_ids": ["location-1"],
            "time_slots": [],  # Empty list
            "number_of_days": 1
        }
        
        response = client.post(
            f"/conventions/test-convention-id/bulk-slots",
            json=request_data
        )
        
        assert response.status_code == 422  # Validation error

def test_create_bulk_slots_verify_day_numbering(override_get_db, sample_data, db_session):
    """Test that bulk slot creation correctly sets day numbers."""
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["admin_user"]
        
        request_data = {
            "convention_id": "test-convention-id",
            "location_ids": ["location-1"],
            "time_slots": [
                {"start_time": "09:00", "end_time": "10:30"}
            ],
            "number_of_days": 3
        }
        
        response = client.post(
            f"/conventions/test-convention-id/bulk-slots",
            json=request_data
        )
        
        assert response.status_code == 200
        
        # Verify day numbers in database
        slots_day_1 = db_session.query(EventSlot).filter(
            EventSlot.convention_id == "test-convention-id",
            EventSlot.day_number == 1
        ).count()
        slots_day_2 = db_session.query(EventSlot).filter(
            EventSlot.convention_id == "test-convention-id",
            EventSlot.day_number == 2
        ).count()
        slots_day_3 = db_session.query(EventSlot).filter(
            EventSlot.convention_id == "test-convention-id",
            EventSlot.day_number == 3
        ).count()
        
        assert slots_day_1 == 1
        assert slots_day_2 == 1
        assert slots_day_3 == 1