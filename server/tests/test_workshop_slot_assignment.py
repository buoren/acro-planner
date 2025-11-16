"""
Tests for workshop-to-slot assignment endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ulid import ULID

from main import app
from database import get_db, SessionLocal
from models import (
    Users, Admins, Hosts, Attendees, Events, EventSlot, HostEvents, 
    Conventions, Locations, Capabilities
)

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
        id=str(ULID()),
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
    
    # Create host user
    host_user = Users(
        id=str(ULID()),
        email="host@test.com",
        name="Host User",
        auth_provider="test",
        auth_provider_id="host123",
        is_active=True
    )
    db_session.add(host_user)
    
    # Create attendee for host (required for host creation)
    host_attendee = Attendees(
        id=str(ULID()),
        user_id=host_user.id,
        convention_id="test-convention-id",
        is_registered=True,
        capability_ids=[]
    )
    db_session.add(host_attendee)
    
    host = Hosts(
        id=str(ULID()),
        user_id=host_user.id,
        attendee_id=host_attendee.id,
        available_slot_ids=[]
    )
    db_session.add(host)
    
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
    
    # Create location
    location = Locations(
        id=str(ULID()),
        name="Test Location",
        convention_id="test-convention-id",
        description="Test Location Description",
        capacity=50,
        address="123 Test St",
        equipment_ids=[]
    )
    db_session.add(location)
    
    # Create workshop/event
    workshop = Events(
        id=str(ULID()),
        name="Test Workshop",
        description="Test Workshop Description",
        max_students=20,
        prerequisite_ids=[],
        equipment_ids=[],
        convention_id="test-convention-id"
    )
    db_session.add(workshop)
    
    # Create host-event relationship
    host_event = HostEvents(
        id=str(ULID()),
        host_id=host.id,
        event_id=workshop.id
    )
    db_session.add(host_event)
    
    # Create event slots
    slot1 = EventSlot(
        id="slot-1",
        convention_id="test-convention-id",
        location_id=location.id,
        start_time=datetime.now() + timedelta(hours=1),
        end_time=datetime.now() + timedelta(hours=2),
        day_number=1,
        event_id=None  # Available slot
    )
    db_session.add(slot1)
    
    slot2 = EventSlot(
        id="slot-2",
        convention_id="test-convention-id",
        location_id=location.id,
        start_time=datetime.now() + timedelta(hours=3),
        end_time=datetime.now() + timedelta(hours=4),
        day_number=1,
        event_id=None  # Available slot
    )
    db_session.add(slot2)
    
    # Update host availability to include these slots
    host.available_slot_ids = ["slot-1", "slot-2"]
    
    db_session.commit()
    
    return {
        "admin_user": admin_user,
        "host_user": host_user,
        "host": host,
        "workshop": workshop,
        "location": location,
        "slot1": slot1,
        "slot2": slot2,
        "convention": convention
    }

def test_assign_workshop_to_slot_success(override_get_db, sample_data):
    """Test successful workshop-to-slot assignment."""
    # Mock authentication for host user
    with client:
        # Mock the get_current_user to return our host user
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["host_user"]
        
        response = client.post(
            f"/workshops/{sample_data['workshop'].id}/assign-slot",
            json={
                "workshop_id": sample_data['workshop'].id,
                "event_slot_id": "slot-1"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["workshop"]["id"] == sample_data['workshop'].id
        assert data["event_slot"]["id"] == "slot-1"
        assert data["assigned_at"] is not None

def test_assign_workshop_to_slot_admin(override_get_db, sample_data):
    """Test workshop assignment by admin user."""
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["admin_user"]
        
        response = client.post(
            f"/workshops/{sample_data['workshop'].id}/assign-slot",
            json={
                "workshop_id": sample_data['workshop'].id,
                "event_slot_id": "slot-2"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["workshop"]["id"] == sample_data['workshop'].id
        assert data["event_slot"]["id"] == "slot-2"

def test_assign_workshop_to_nonexistent_slot(override_get_db, sample_data):
    """Test assignment to non-existent slot."""
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["host_user"]
        
        response = client.post(
            f"/workshops/{sample_data['workshop'].id}/assign-slot",
            json={
                "workshop_id": sample_data['workshop'].id,
                "event_slot_id": "nonexistent-slot"
            }
        )
        
        assert response.status_code == 404
        assert "Event slot not found" in response.json()["detail"]

def test_assign_nonexistent_workshop(override_get_db, sample_data):
    """Test assignment of non-existent workshop."""
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["host_user"]
        
        response = client.post(
            "/workshops/nonexistent-workshop/assign-slot",
            json={
                "workshop_id": "nonexistent-workshop",
                "event_slot_id": "slot-1"
            }
        )
        
        assert response.status_code == 404
        assert "Workshop not found" in response.json()["detail"]

def test_unassign_workshop_from_slot(override_get_db, sample_data, db_session):
    """Test unassigning workshop from slot."""
    # First assign the workshop
    slot = db_session.query(EventSlot).filter(EventSlot.id == "slot-1").first()
    slot.event_id = sample_data['workshop'].id
    db_session.commit()
    
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["host_user"]
        
        response = client.delete(
            f"/workshops/{sample_data['workshop'].id}/unassign-slot/slot-1"
        )
        
        assert response.status_code == 200
        assert "unassigned" in response.json()["message"].lower()

def test_get_workshop_slots(override_get_db, sample_data, db_session):
    """Test getting all slots for a workshop."""
    # Assign workshop to multiple slots
    slot1 = db_session.query(EventSlot).filter(EventSlot.id == "slot-1").first()
    slot2 = db_session.query(EventSlot).filter(EventSlot.id == "slot-2").first()
    slot1.event_id = sample_data['workshop'].id
    slot2.event_id = sample_data['workshop'].id
    db_session.commit()
    
    response = client.get(f"/workshops/{sample_data['workshop'].id}/slots")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(slot["id"] == "slot-1" for slot in data)
    assert any(slot["id"] == "slot-2" for slot in data)

def test_get_slot_workshop(override_get_db, sample_data, db_session):
    """Test getting workshop assigned to a slot."""
    # Assign workshop to slot
    slot = db_session.query(EventSlot).filter(EventSlot.id == "slot-1").first()
    slot.event_id = sample_data['workshop'].id
    db_session.commit()
    
    response = client.get("/event-slots/slot-1/workshop")
    
    assert response.status_code == 200
    data = response.json()
    assert data["event_slot"]["id"] == "slot-1"
    assert data["workshop"]["id"] == sample_data['workshop'].id
    assert data["workshop"]["name"] == "Test Workshop"

def test_get_slot_workshop_empty_slot(override_get_db, sample_data):
    """Test getting workshop for empty slot."""
    response = client.get("/event-slots/slot-1/workshop")
    
    assert response.status_code == 200
    data = response.json()
    assert data["event_slot"]["id"] == "slot-1"
    assert data["workshop"] is None

def test_list_available_event_slots(override_get_db, sample_data, db_session):
    """Test listing only available (empty) event slots."""
    # Assign one slot to a workshop
    slot1 = db_session.query(EventSlot).filter(EventSlot.id == "slot-1").first()
    slot1.event_id = sample_data['workshop'].id
    db_session.commit()
    
    response = client.get("/event-slots/?available_only=true")
    
    assert response.status_code == 200
    data = response.json()
    # Should only return slot-2 (slot-1 is assigned)
    assert len(data) == 1
    assert data[0]["id"] == "slot-2"

def test_assign_workshop_host_not_available(override_get_db, sample_data, db_session):
    """Test assignment when host is not available for the slot."""
    # Remove slot-1 from host availability
    host = db_session.query(Hosts).filter(Hosts.id == sample_data['host'].id).first()
    host.available_slot_ids = ["slot-2"]  # Only slot-2 available
    db_session.commit()
    
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["host_user"]
        
        response = client.post(
            f"/workshops/{sample_data['workshop'].id}/assign-slot",
            json={
                "workshop_id": sample_data['workshop'].id,
                "event_slot_id": "slot-1"  # Host not available for this slot
            }
        )
        
        assert response.status_code == 400
        assert "not available for this time slot" in response.json()["detail"]

def test_assign_workshop_to_occupied_slot(override_get_db, sample_data, db_session):
    """Test assignment to slot already assigned to another workshop."""
    # Create another workshop
    other_workshop = Events(
        id=str(ULID()),
        name="Other Workshop",
        description="Other Description",
        max_students=15,
        prerequisite_ids=[],
        equipment_ids=[],
        convention_id="test-convention-id"
    )
    db_session.add(other_workshop)
    
    # Assign slot-1 to other workshop
    slot = db_session.query(EventSlot).filter(EventSlot.id == "slot-1").first()
    slot.event_id = other_workshop.id
    db_session.commit()
    
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["host_user"]
        
        response = client.post(
            f"/workshops/{sample_data['workshop'].id}/assign-slot",
            json={
                "workshop_id": sample_data['workshop'].id,
                "event_slot_id": "slot-1"
            }
        )
        
        assert response.status_code == 409
        assert "already assigned to another workshop" in response.json()["detail"]

def test_unauthorized_assignment(override_get_db, sample_data, db_session):
    """Test that non-host/non-admin users cannot assign workshops."""
    # Create regular user
    regular_user = Users(
        id=str(ULID()),
        email="user@test.com",
        name="Regular User",
        auth_provider="test",
        auth_provider_id="user123",
        is_active=True
    )
    db_session.add(regular_user)
    db_session.commit()
    
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: regular_user
        
        response = client.post(
            f"/workshops/{sample_data['workshop'].id}/assign-slot",
            json={
                "workshop_id": sample_data['workshop'].id,
                "event_slot_id": "slot-1"
            }
        )
        
        assert response.status_code == 403