"""
Tests for workshop management API endpoints.
"""

import pytest
from ulid import ULID
from datetime import datetime, timedelta


def test_create_workshop_host_allowed(authenticated_client_host, db_session):
    """Test that hosts can create workshops."""
    from models import Hosts, Attendees
    
    # Get the host's ID
    host_user = authenticated_client_host._transport.app.dependency_overrides[
        list(authenticated_client_host._transport.app.dependency_overrides.keys())[0]
    ](None)
    
    # Create host record
    attendee = Attendees(
        id=str(ULID()),
        user_id=host_user["id"],
        convention_id=str(ULID())
    )
    host = Hosts(
        id=str(ULID()),
        attendee_id=attendee.id,
        user_id=host_user["id"]
    )
    db_session.add_all([attendee, host])
    db_session.commit()
    
    workshop_data = {
        "name": "Partner Acrobatics Basics",
        "description": "Learn the fundamentals of partner acrobatics",
        "host_id": host.id,
        "max_students": 12,
        "prerequisite_ids": [],
        "equipment_ids": []
    }
    
    response = authenticated_client_host.post("/workshops/", json=workshop_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Partner Acrobatics Basics"
    assert data["max_students"] == 12


def test_list_workshops_public(test_client, db_session):
    """Test that listing workshops is public."""
    from models import Events, Conventions
    
    conv_id = str(ULID())
    convention = Conventions(
        id=conv_id,
        name="Test Convention",
        is_active=True
    )
    workshop1 = Events(
        id=str(ULID()),
        name="Morning Flow",
        description="Morning yoga flow",
        convention_id=conv_id,
        max_students=20
    )
    workshop2 = Events(
        id=str(ULID()),
        name="Evening Stretch",
        description="Evening stretch session",
        convention_id=conv_id,
        max_students=15
    )
    
    db_session.add_all([convention, workshop1, workshop2])
    db_session.commit()
    
    response = test_client.get("/workshops/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_filter_workshops_by_space(test_client, db_session):
    """Test filtering workshops by available space."""
    from models import Events, Selections
    
    # Create workshop with limited space
    workshop_id = str(ULID())
    workshop = Events(
        id=workshop_id,
        name="Small Group",
        description="Small group session",
        convention_id=str(ULID()),
        max_students=2
    )
    
    # Fill it up with committed students
    selection1 = Selections(
        id=str(ULID()),
        attendee_id=str(ULID()),
        event_id=workshop_id,
        commitment_level="committed"
    )
    selection2 = Selections(
        id=str(ULID()),
        attendee_id=str(ULID()),
        event_id=workshop_id,
        commitment_level="committed"
    )
    
    db_session.add_all([workshop, selection1, selection2])
    db_session.commit()
    
    # Should not show up when filtering by has_space
    response = test_client.get("/workshops/?has_space=true")
    assert response.status_code == 200
    data = response.json()
    assert not any(w["id"] == workshop_id for w in data)


def test_update_workshop_owner_only(authenticated_client_host, db_session):
    """Test that only the workshop owner (or admin) can update it."""
    from models import Events, HostEvents, Hosts, Attendees
    
    # Get host user
    host_user = authenticated_client_host._transport.app.dependency_overrides[
        list(authenticated_client_host._transport.app.dependency_overrides.keys())[0]
    ](None)
    
    # Create host and workshop
    attendee = Attendees(
        id=str(ULID()),
        user_id=host_user["id"],
        convention_id=str(ULID())
    )
    host = Hosts(
        id=str(ULID()),
        attendee_id=attendee.id,
        user_id=host_user["id"]
    )
    workshop = Events(
        id=str(ULID()),
        name="Original Workshop",
        description="Original description",
        convention_id=str(ULID()),
        max_students=10
    )
    host_event = HostEvents(
        id=str(ULID()),
        host_id=host.id,
        event_id=workshop.id
    )
    
    db_session.add_all([attendee, host, workshop, host_event])
    db_session.commit()
    
    update_data = {
        "name": "Updated Workshop",
        "max_students": 15
    }
    
    response = authenticated_client_host.put(f"/workshops/{workshop.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Workshop"
    assert data["max_students"] == 15


def test_add_prerequisite_to_workshop(authenticated_client_host, db_session):
    """Test adding a prerequisite to a workshop."""
    from models import Events, Capabilities, HostEvents, Hosts, Attendees
    
    # Get host user
    host_user = authenticated_client_host._transport.app.dependency_overrides[
        list(authenticated_client_host._transport.app.dependency_overrides.keys())[0]
    ](None)
    
    # Create prerequisite
    prereq_id = str(ULID())
    prerequisite = Capabilities(
        id=prereq_id,
        name="Balance",
        description="Basic balance skills"
    )
    
    # Create workshop
    attendee = Attendees(
        id=str(ULID()),
        user_id=host_user["id"],
        convention_id=str(ULID())
    )
    host = Hosts(
        id=str(ULID()),
        attendee_id=attendee.id,
        user_id=host_user["id"]
    )
    workshop = Events(
        id=str(ULID()),
        name="Advanced Workshop",
        description="Advanced techniques",
        convention_id=str(ULID()),
        max_students=10,
        prerequisite_ids=[]
    )
    host_event = HostEvents(
        id=str(ULID()),
        host_id=host.id,
        event_id=workshop.id
    )
    
    db_session.add_all([prerequisite, attendee, host, workshop, host_event])
    db_session.commit()
    
    response = authenticated_client_host.post(
        f"/workshops/{workshop.id}/add-prerequisite",
        params={"prerequisite_id": prereq_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["prerequisites"]) == 1
    assert data["prerequisites"][0]["id"] == prereq_id


def test_add_equipment_to_workshop(authenticated_client_host, db_session):
    """Test adding equipment requirement to a workshop."""
    from models import Events, Equipment, HostEvents, Hosts, Attendees
    
    # Get host user
    host_user = authenticated_client_host._transport.app.dependency_overrides[
        list(authenticated_client_host._transport.app.dependency_overrides.keys())[0]
    ](None)
    
    # Create equipment
    equip_id = str(ULID())
    equipment = Equipment(
        id=equip_id,
        name="Yoga Mats",
        quantity=20,
        location_id=str(ULID()),
        convention_id=str(ULID())
    )
    
    # Create workshop
    attendee = Attendees(
        id=str(ULID()),
        user_id=host_user["id"],
        convention_id=str(ULID())
    )
    host = Hosts(
        id=str(ULID()),
        attendee_id=attendee.id,
        user_id=host_user["id"]
    )
    workshop = Events(
        id=str(ULID()),
        name="Yoga Workshop",
        description="Yoga techniques",
        convention_id=str(ULID()),
        max_students=15,
        equipment_ids=[]
    )
    host_event = HostEvents(
        id=str(ULID()),
        host_id=host.id,
        event_id=workshop.id
    )
    
    db_session.add_all([equipment, attendee, host, workshop, host_event])
    db_session.commit()
    
    response = authenticated_client_host.post(
        f"/workshops/{workshop.id}/add-equipment",
        params={"equipment_id": equip_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["equipment"]) == 1
    assert data["equipment"][0]["id"] == equip_id


def test_set_host_availability(authenticated_client_host, db_session):
    """Test setting host availability for event slots."""
    from models import Hosts, Attendees, EventSlot
    from datetime import datetime
    
    # Get host user
    host_user = authenticated_client_host._transport.app.dependency_overrides[
        list(authenticated_client_host._transport.app.dependency_overrides.keys())[0]
    ](None)
    
    # Create host and event slots
    attendee = Attendees(
        id=str(ULID()),
        user_id=host_user["id"],
        convention_id=str(ULID())
    )
    host = Hosts(
        id=str(ULID()),
        attendee_id=attendee.id,
        user_id=host_user["id"]
    )
    slot1_id = str(ULID())
    slot2_id = str(ULID())
    slot1 = EventSlot(
        id=slot1_id,
        convention_id=str(ULID()),
        location_id=str(ULID()),
        start_time=datetime.now() + timedelta(days=1),
        end_time=datetime.now() + timedelta(days=1, hours=1),
        day_number=1
    )
    slot2 = EventSlot(
        id=slot2_id,
        convention_id=str(ULID()),
        location_id=str(ULID()),
        start_time=datetime.now() + timedelta(days=2),
        end_time=datetime.now() + timedelta(days=2, hours=1),
        day_number=2
    )
    
    db_session.add_all([attendee, host, slot1, slot2])
    db_session.commit()
    
    availability_data = {
        "host_id": host.id,
        "event_slot_ids": [slot1_id, slot2_id]
    }
    
    response = authenticated_client_host.post("/workshops/host-availability", json=availability_data)
    assert response.status_code == 200
    data = response.json()
    assert data["host_id"] == host.id
    assert len(data["available_slots"]) == 2


def test_get_host_availability(test_client, db_session):
    """Test getting host availability."""
    from models import Hosts, Attendees, EventSlot, Locations
    from datetime import datetime
    
    # Create host with availability
    host_id = str(ULID())
    slot_id = str(ULID())
    loc_id = str(ULID())
    
    attendee = Attendees(
        id=str(ULID()),
        user_id=str(ULID())
    )
    location = Locations(
        id=loc_id,
        name="Studio A",
        convention_id=str(ULID())
    )
    host = Hosts(
        id=host_id,
        attendee_id=attendee.id,
        user_id=attendee.user_id,
        available_slot_ids=[slot_id]
    )
    slot = EventSlot(
        id=slot_id,
        convention_id=str(ULID()),
        location_id=loc_id,
        start_time=datetime.now() + timedelta(days=1),
        end_time=datetime.now() + timedelta(days=1, hours=1),
        day_number=1
    )
    
    db_session.add_all([attendee, location, host, slot])
    db_session.commit()
    
    response = test_client.get(f"/workshops/hosts/{host_id}/availability")
    assert response.status_code == 200
    data = response.json()
    assert data["host_id"] == host_id
    assert len(data["available_slots"]) == 1


def test_workshop_share_link(test_client, db_session):
    """Test getting a shareable link for a workshop."""
    from models import Events
    
    workshop_id = str(ULID())
    workshop = Events(
        id=workshop_id,
        name="Share This Workshop",
        description="Great workshop to share",
        convention_id=str(ULID()),
        max_students=20
    )
    
    db_session.add(workshop)
    db_session.commit()
    
    response = test_client.get(f"/workshops/{workshop_id}/share")
    assert response.status_code == 200
    data = response.json()
    assert data["workshop_id"] == workshop_id
    assert data["workshop_name"] == "Share This Workshop"
    assert "share_url" in data
    assert workshop_id in data["share_url"]


def test_delete_workshop(authenticated_client_host, db_session):
    """Test deleting a workshop."""
    from models import Events, HostEvents, Hosts, Attendees, Selections, EventSlot
    
    # Get host user
    host_user = authenticated_client_host._transport.app.dependency_overrides[
        list(authenticated_client_host._transport.app.dependency_overrides.keys())[0]
    ](None)
    
    # Create workshop with dependencies
    workshop_id = str(ULID())
    host_id = str(ULID())
    slot_id = str(ULID())
    selection_id = str(ULID())
    
    attendee = Attendees(
        id=str(ULID()),
        user_id=host_user["id"],
        convention_id=str(ULID())
    )
    host = Hosts(
        id=host_id,
        attendee_id=attendee.id,
        user_id=host_user["id"]
    )
    workshop = Events(
        id=workshop_id,
        name="Delete Me",
        description="Workshop to delete",
        convention_id=str(ULID()),
        max_students=10
    )
    host_event = HostEvents(
        id=str(ULID()),
        host_id=host_id,
        event_id=workshop_id
    )
    selection = Selections(
        id=selection_id,
        attendee_id=str(ULID()),
        event_id=workshop_id
    )
    slot = EventSlot(
        id=slot_id,
        convention_id=str(ULID()),
        location_id=str(ULID()),
        event_id=workshop_id,
        start_time=datetime.now(),
        end_time=datetime.now() + timedelta(hours=1),
        day_number=1
    )
    
    db_session.add_all([attendee, host, workshop, host_event, selection, slot])
    db_session.commit()
    
    response = authenticated_client_host.delete(f"/workshops/{workshop_id}")
    assert response.status_code == 200
    
    # Verify workshop is deleted
    deleted_workshop = db_session.query(Events).filter(Events.id == workshop_id).first()
    assert deleted_workshop is None
    
    # Verify related data is cleaned up
    deleted_host_event = db_session.query(HostEvents).filter(HostEvents.event_id == workshop_id).first()
    assert deleted_host_event is None
    
    deleted_selection = db_session.query(Selections).filter(Selections.id == selection_id).first()
    assert deleted_selection is None
    
    # Event slot should have event_id cleared
    db_session.refresh(slot)
    assert slot.event_id is None