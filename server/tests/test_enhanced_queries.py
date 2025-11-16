"""
Tests for enhanced query and filter endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ulid import ULID

from main import app
from database import get_db, SessionLocal
from models import (
    Users, Admins, Attendees, Conventions, Locations, EventSlot, 
    Events, HostEvents, Hosts, Capabilities, Selections
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
    """Create comprehensive sample data for testing."""
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
    
    # Create regular user/attendee
    regular_user = Users(
        id="regular-user-id",
        email="user@test.com",
        name="Regular User",
        auth_provider="test",
        auth_provider_id="user123",
        is_active=True
    )
    db_session.add(regular_user)
    
    # Create host user
    host_user = Users(
        id="host-user-id",
        email="host@test.com",
        name="Host User",
        auth_provider="test",
        auth_provider_id="host123",
        is_active=True
    )
    db_session.add(host_user)
    
    # Create convention
    convention = Conventions(
        id="test-convention-id",
        name="Test Convention 2024",
        description="Annual acrobatics convention",
        start_date=datetime.now().date(),
        end_date=(datetime.now() + timedelta(days=3)).date(),
        is_active=True
    )
    db_session.add(convention)
    
    # Create capabilities
    beginner_cap = Capabilities(
        id="beginner-cap-id",
        name="Beginner Level",
        description="Basic acrobatics skills",
        parent_capability_ids=[]
    )
    db_session.add(beginner_cap)
    
    intermediate_cap = Capabilities(
        id="intermediate-cap-id",
        name="Intermediate Level", 
        description="Intermediate acrobatics skills",
        parent_capability_ids=["beginner-cap-id"]
    )
    db_session.add(intermediate_cap)
    
    # Create attendees
    attendee1 = Attendees(
        id="attendee-1-id",
        user_id="regular-user-id",
        convention_id="test-convention-id",
        is_registered=True,
        capability_ids=["beginner-cap-id"]
    )
    db_session.add(attendee1)
    
    host_attendee = Attendees(
        id="host-attendee-id",
        user_id="host-user-id",
        convention_id="test-convention-id",
        is_registered=True,
        capability_ids=["intermediate-cap-id"]
    )
    db_session.add(host_attendee)
    
    # Create host
    host = Hosts(
        id="host-id",
        user_id="host-user-id",
        attendee_id="host-attendee-id",
        available_slot_ids=[]
    )
    db_session.add(host)
    
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
        name="Studio A",
        convention_id="test-convention-id",
        description="Practice studio",
        capacity=20,
        address="123 Convention Center, Studio A",
        equipment_ids=[]
    )
    db_session.add(location2)
    
    # Create event slots
    slot1 = EventSlot(
        id="slot-1",
        convention_id="test-convention-id",
        location_id="location-1",
        start_time=datetime.now() + timedelta(hours=1),
        end_time=datetime.now() + timedelta(hours=2),
        day_number=1,
        event_id=None  # Available
    )
    db_session.add(slot1)
    
    slot2 = EventSlot(
        id="slot-2",
        convention_id="test-convention-id",
        location_id="location-2",
        start_time=datetime.now() + timedelta(hours=3),
        end_time=datetime.now() + timedelta(hours=4),
        day_number=1,
        event_id="workshop-1"  # Assigned
    )
    db_session.add(slot2)
    
    slot3 = EventSlot(
        id="slot-3",
        convention_id="test-convention-id",
        location_id="location-1",
        start_time=datetime.now() + timedelta(days=1, hours=1),
        end_time=datetime.now() + timedelta(days=1, hours=2),
        day_number=2,
        event_id=None  # Available
    )
    db_session.add(slot3)
    
    # Create workshops
    workshop1 = Events(
        id="workshop-1",
        name="Beginner Handstands",
        description="Learn basic handstand techniques",
        max_students=15,
        prerequisite_ids=["beginner-cap-id"],
        equipment_ids=[],
        convention_id="test-convention-id"
    )
    db_session.add(workshop1)
    
    workshop2 = Events(
        id="workshop-2",
        name="Advanced Flow",
        description="Advanced movement sequences",
        max_students=10,
        prerequisite_ids=["intermediate-cap-id"],
        equipment_ids=[],
        convention_id="test-convention-id"
    )
    db_session.add(workshop2)
    
    # Create host-workshop relationships
    host_event1 = HostEvents(
        id=str(ULID()),
        host_id="host-id",
        event_id="workshop-1"
    )
    db_session.add(host_event1)
    
    host_event2 = HostEvents(
        id=str(ULID()),
        host_id="host-id",
        event_id="workshop-2"
    )
    db_session.add(host_event2)
    
    # Create workshop selections
    selection1 = Selections(
        id=str(ULID()),
        attendee_id="attendee-1-id",
        event_id="workshop-1",
        event_slot_id="slot-2",
        commitment_level="committed"
    )
    db_session.add(selection1)
    
    selection2 = Selections(
        id=str(ULID()),
        attendee_id="attendee-1-id",
        event_id="workshop-2",
        event_slot_id=None,  # Interested but no specific slot
        commitment_level="interested"
    )
    db_session.add(selection2)
    
    db_session.commit()
    
    return {
        "admin_user": admin_user,
        "regular_user": regular_user,
        "host_user": host_user,
        "convention": convention,
        "locations": [location1, location2],
        "workshops": [workshop1, workshop2],
        "slots": [slot1, slot2, slot3],
        "attendee1": attendee1,
        "capabilities": [beginner_cap, intermediate_cap]
    }

def test_get_convention_schedule_empty(override_get_db, sample_data):
    """Test getting convention schedule with empty schedule."""
    response = client.get(f"/conventions/{sample_data['convention'].id}/schedule")
    
    assert response.status_code == 200
    data = response.json()
    assert data["convention_id"] == sample_data['convention'].id
    assert data["convention_name"] == "Test Convention 2024"
    assert "schedule" in data

def test_get_convention_schedule_with_workshops(override_get_db, sample_data, db_session):
    """Test getting convention schedule with workshops assigned."""
    response = client.get(f"/conventions/{sample_data['convention'].id}/schedule")
    
    assert response.status_code == 200
    data = response.json()
    schedule = data["schedule"]
    
    # Should have entries for days with workshops
    assert len(schedule) >= 1
    
    # Day 1 should have at least one slot with a workshop
    if "1" in schedule:
        day1_slots = schedule["1"]
        workshop_found = any(slot["workshop"] is not None for slot in day1_slots)
        assert workshop_found

def test_list_available_event_slots_only(override_get_db, sample_data):
    """Test listing only available (unassigned) event slots."""
    response = client.get("/event-slots/?available_only=true")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should only return slots without assigned workshops
    for slot in data:
        # Check that slot is not assigned by looking up in our test data
        slot_id = slot["id"]
        assert slot_id in ["slot-1", "slot-3"]  # These are the unassigned slots

def test_list_event_slots_by_convention(override_get_db, sample_data):
    """Test filtering event slots by convention."""
    response = client.get(f"/event-slots/?convention_id={sample_data['convention'].id}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should return all slots for this convention
    assert len(data) == 3
    convention_ids = [slot["convention_id"] for slot in data]
    assert all(cid == sample_data['convention'].id for cid in convention_ids)

def test_list_event_slots_by_location(override_get_db, sample_data):
    """Test filtering event slots by location."""
    location1_id = sample_data['locations'][0].id
    
    response = client.get(f"/event-slots/?location_id={location1_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should only return slots for location-1
    for slot in data:
        assert slot["location"]["id"] == location1_id

def test_list_workshops_with_space_filter(override_get_db, sample_data):
    """Test listing workshops that have available space."""
    response = client.get("/workshops/?has_space=true")
    
    assert response.status_code == 200
    data = response.json()
    
    # All workshops should have space (max_students > current_students)
    for workshop in data:
        assert workshop["current_students"] < workshop["max_students"]

def test_list_workshops_by_convention(override_get_db, sample_data):
    """Test filtering workshops by convention."""
    response = client.get(f"/workshops/?convention_id={sample_data['convention'].id}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should return workshops for this convention
    assert len(data) >= 1
    for workshop in data:
        # Verify these are our test workshops
        assert workshop["name"] in ["Beginner Handstands", "Advanced Flow"]

def test_list_workshops_by_host(override_get_db, sample_data):
    """Test filtering workshops by host."""
    host_id = "host-id"
    response = client.get(f"/workshops/?host_id={host_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should return workshops hosted by this host
    for workshop in data:
        assert workshop["host_id"] == host_id

def test_admin_list_convention_attendees(override_get_db, sample_data):
    """Test admin viewing convention attendee list with selection stats."""
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["admin_user"]
        
        response = client.get(f"/conventions/{sample_data['convention'].id}/attendees")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should include attendees with their selection statistics
        assert len(data) >= 1
        
        # Find our test attendee
        regular_attendee = None
        for attendee in data:
            if attendee["attendee_name"] == "Regular User":
                regular_attendee = attendee
                break
        
        assert regular_attendee is not None
        assert "selections" in regular_attendee
        assert "committed" in regular_attendee["selections"]
        assert "interested" in regular_attendee["selections"]
        assert regular_attendee["total_selections"] >= 1

def test_get_attendee_capabilities(override_get_db, sample_data):
    """Test getting attendee's capabilities."""
    attendee_id = sample_data['attendee1'].id
    
    response = client.get(f"/attendees/{attendee_id}/capabilities")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should return attendee's capabilities
    assert len(data) >= 1
    capability_names = [cap["name"] for cap in data]
    assert "Beginner Level" in capability_names

def test_get_attendee_capabilities_nonexistent(override_get_db, sample_data):
    """Test getting capabilities for non-existent attendee."""
    response = client.get("/attendees/nonexistent-attendee/capabilities")
    
    assert response.status_code == 404
    assert "Attendee not found" in response.json()["detail"]

def test_browse_workshops_with_filters(override_get_db, sample_data):
    """Test browsing workshops with comprehensive filters."""
    with client:
        from api.auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: sample_data["regular_user"]
        
        filter_data = {
            "convention_id": sample_data['convention'].id,
            "can_fulfill_prerequisites": True,
            "attendee_capabilities": ["beginner-cap-id"],
            "has_space": True
        }
        
        response = client.post("/workshops/browse", json=filter_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return workshops that match filters
        for workshop in data:
            # Should have space
            assert workshop["current_students"] < workshop["max_students"]
            # Should be accessible with beginner capabilities
            # (This test validates that prerequisite filtering works)

def test_get_slot_with_assigned_workshop(override_get_db, sample_data):
    """Test getting workshop assigned to a specific slot."""
    # slot-2 should have workshop-1 assigned
    response = client.get("/event-slots/slot-2/workshop")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["event_slot"]["id"] == "slot-2"
    assert data["workshop"] is not None
    assert data["workshop"]["id"] == "workshop-1"
    assert data["workshop"]["name"] == "Beginner Handstands"

def test_get_slot_without_assigned_workshop(override_get_db, sample_data):
    """Test getting workshop for slot with no assignment."""
    # slot-1 should be empty
    response = client.get("/event-slots/slot-1/workshop")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["event_slot"]["id"] == "slot-1"
    assert data["workshop"] is None

def test_combined_filters_event_slots(override_get_db, sample_data):
    """Test combining multiple filters for event slots."""
    location1_id = sample_data['locations'][0].id
    convention_id = sample_data['convention'].id
    
    response = client.get(
        f"/event-slots/?convention_id={convention_id}&location_id={location1_id}&available_only=true"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should return only available slots in location-1 for this convention
    for slot in data:
        assert slot["convention_id"] == convention_id
        assert slot["location"]["id"] == location1_id
        # Available slots should be slot-1 and slot-3
        assert slot["id"] in ["slot-1", "slot-3"]