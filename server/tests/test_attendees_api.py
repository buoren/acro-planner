"""
Tests for attendee selection and schedule management API endpoints.
"""

import pytest
from ulid import ULID
from datetime import datetime, timedelta


def test_select_workshop_as_attendee(authenticated_client_attendee, db_session):
    """Test that attendees can select workshops."""
    from models import Events, EventSlot, Attendees
    
    # Get attendee user
    attendee_user = authenticated_client_attendee._transport.app.dependency_overrides[
        list(authenticated_client_attendee._transport.app.dependency_overrides.keys())[0]
    ](None)
    
    # Create attendee, workshop and event slot
    attendee = Attendees(
        id=str(ULID()),
        user_id=attendee_user["id"],
        convention_id=str(ULID())
    )
    workshop_id = str(ULID())
    slot_id = str(ULID())
    
    workshop = Events(
        id=workshop_id,
        name="Test Workshop",
        description="Test description",
        convention_id=attendee.convention_id,
        max_students=10
    )
    slot = EventSlot(
        id=slot_id,
        convention_id=attendee.convention_id,
        location_id=str(ULID()),
        start_time=datetime.now() + timedelta(days=1),
        end_time=datetime.now() + timedelta(days=1, hours=1),
        event_id=workshop_id,
        day_number=1
    )
    
    db_session.add_all([attendee, workshop, slot])
    db_session.commit()
    
    selection_data = {
        "attendee_id": attendee.id,
        "workshop_id": workshop_id,
        "event_slot_id": slot_id,
        "commitment_level": "interested"
    }
    
    response = authenticated_client_attendee.post("/attendees/selections", json=selection_data)
    assert response.status_code == 200
    data = response.json()
    assert data["workshop"]["id"] == workshop_id
    assert data["commitment_level"] == "interested"


def test_cannot_double_select_same_workshop(authenticated_client_attendee, db_session):
    """Test that attendees cannot select the same workshop twice for the same slot."""
    from models import Events, EventSlot, Attendees, Selections
    
    # Get attendee user
    attendee_user = authenticated_client_attendee._transport.app.dependency_overrides[
        list(authenticated_client_attendee._transport.app.dependency_overrides.keys())[0]
    ](None)
    
    attendee = Attendees(
        id=str(ULID()),
        user_id=attendee_user["id"],
        convention_id=str(ULID())
    )
    workshop_id = str(ULID())
    slot_id = str(ULID())
    
    workshop = Events(
        id=workshop_id,
        name="Popular Workshop",
        description="Everyone wants this",
        convention_id=attendee.convention_id,
        max_students=10
    )
    slot = EventSlot(
        id=slot_id,
        convention_id=attendee.convention_id,
        location_id=str(ULID()),
        start_time=datetime.now() + timedelta(days=1),
        end_time=datetime.now() + timedelta(days=1, hours=1),
        event_id=workshop_id,
        day_number=1
    )
    
    # Create existing selection
    existing_selection = Selections(
        id=str(ULID()),
        attendee_id=attendee.id,
        event_id=workshop_id,
        event_slot_id=slot_id,
        commitment_level="interested"
    )
    
    db_session.add_all([attendee, workshop, slot, existing_selection])
    db_session.commit()
    
    # Try to select again
    selection_data = {
        "attendee_id": attendee.id,
        "workshop_id": workshop_id,
        "event_slot_id": slot_id,
        "commitment_level": "maybe"
    }
    
    response = authenticated_client_attendee.post("/attendees/selections", json=selection_data)
    assert response.status_code == 400
    assert "already selected" in response.json()["detail"].lower()


def test_cannot_commit_to_conflicting_workshops(authenticated_client_attendee, db_session):
    """Test that attendees cannot commit to workshops at the same time."""
    from models import Events, EventSlot, Attendees, Selections
    
    # Get attendee user
    attendee_user = authenticated_client_attendee._transport.app.dependency_overrides[
        list(authenticated_client_attendee._transport.app.dependency_overrides.keys())[0]
    ](None)
    
    attendee = Attendees(
        id=str(ULID()),
        user_id=attendee_user["id"],
        convention_id=str(ULID())
    )
    workshop1_id = str(ULID())
    workshop2_id = str(ULID())
    slot_id = str(ULID())  # Same slot for both
    
    workshop1 = Events(
        id=workshop1_id,
        name="Workshop 1",
        description="First workshop",
        convention_id=attendee.convention_id,
        max_students=10
    )
    workshop2 = Events(
        id=workshop2_id,
        name="Workshop 2",
        description="Second workshop",
        convention_id=attendee.convention_id,
        max_students=10
    )
    slot = EventSlot(
        id=slot_id,
        convention_id=attendee.convention_id,
        location_id=str(ULID()),
        start_time=datetime.now() + timedelta(days=1),
        end_time=datetime.now() + timedelta(days=1, hours=1),
        day_number=1
    )
    
    # Already committed to workshop 1
    existing_commitment = Selections(
        id=str(ULID()),
        attendee_id=attendee.id,
        event_id=workshop1_id,
        event_slot_id=slot_id,
        commitment_level="committed"
    )
    
    db_session.add_all([attendee, workshop1, workshop2, slot, existing_commitment])
    db_session.commit()
    
    # Try to commit to workshop 2 at the same time
    selection_data = {
        "attendee_id": attendee.id,
        "workshop_id": workshop2_id,
        "event_slot_id": slot_id,
        "commitment_level": "committed"
    }
    
    response = authenticated_client_attendee.post("/attendees/selections", json=selection_data)
    assert response.status_code == 400
    assert "already committed" in response.json()["detail"].lower()


def test_cannot_commit_to_full_workshop(authenticated_client_attendee, db_session):
    """Test that attendees cannot commit to a full workshop."""
    from models import Events, EventSlot, Attendees, Selections
    
    # Get attendee user
    attendee_user = authenticated_client_attendee._transport.app.dependency_overrides[
        list(authenticated_client_attendee._transport.app.dependency_overrides.keys())[0]
    ](None)
    
    attendee = Attendees(
        id=str(ULID()),
        user_id=attendee_user["id"],
        convention_id=str(ULID())
    )
    workshop_id = str(ULID())
    slot_id = str(ULID())
    
    # Create workshop with only 2 spots
    workshop = Events(
        id=workshop_id,
        name="Small Workshop",
        description="Very limited space",
        convention_id=attendee.convention_id,
        max_students=2
    )
    slot = EventSlot(
        id=slot_id,
        convention_id=attendee.convention_id,
        location_id=str(ULID()),
        start_time=datetime.now() + timedelta(days=1),
        end_time=datetime.now() + timedelta(days=1, hours=1),
        event_id=workshop_id,
        day_number=1
    )
    
    # Fill up the workshop
    selection1 = Selections(
        id=str(ULID()),
        attendee_id=str(ULID()),
        event_id=workshop_id,
        event_slot_id=slot_id,
        commitment_level="committed"
    )
    selection2 = Selections(
        id=str(ULID()),
        attendee_id=str(ULID()),
        event_id=workshop_id,
        event_slot_id=slot_id,
        commitment_level="committed"
    )
    
    db_session.add_all([attendee, workshop, slot, selection1, selection2])
    db_session.commit()
    
    # Try to commit to full workshop
    selection_data = {
        "attendee_id": attendee.id,
        "workshop_id": workshop_id,
        "event_slot_id": slot_id,
        "commitment_level": "committed"
    }
    
    response = authenticated_client_attendee.post("/attendees/selections", json=selection_data)
    assert response.status_code == 400
    assert "workshop is full" in response.json()["detail"].lower()


def test_update_selection_commitment_level(authenticated_client_attendee, db_session):
    """Test updating workshop selection commitment level."""
    from models import Events, EventSlot, Attendees, Selections
    
    # Get attendee user
    attendee_user = authenticated_client_attendee._transport.app.dependency_overrides[
        list(authenticated_client_attendee._transport.app.dependency_overrides.keys())[0]
    ](None)
    
    attendee = Attendees(
        id=str(ULID()),
        user_id=attendee_user["id"],
        convention_id=str(ULID())
    )
    workshop_id = str(ULID())
    slot_id = str(ULID())
    selection_id = str(ULID())
    
    workshop = Events(
        id=workshop_id,
        name="Flexible Workshop",
        description="Can change commitment",
        convention_id=attendee.convention_id,
        max_students=10
    )
    slot = EventSlot(
        id=slot_id,
        convention_id=attendee.convention_id,
        location_id=str(ULID()),
        start_time=datetime.now() + timedelta(days=1),
        end_time=datetime.now() + timedelta(days=1, hours=1),
        event_id=workshop_id,
        day_number=1
    )
    selection = Selections(
        id=selection_id,
        attendee_id=attendee.id,
        event_id=workshop_id,
        event_slot_id=slot_id,
        commitment_level="maybe"
    )
    
    db_session.add_all([attendee, workshop, slot, selection])
    db_session.commit()
    
    # Update to committed
    update_data = {
        "commitment_level": "committed"
    }
    
    response = authenticated_client_attendee.put(f"/attendees/selections/{selection_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["commitment_level"] == "committed"


def test_remove_workshop_selection(authenticated_client_attendee, db_session):
    """Test removing a workshop selection."""
    from models import Events, EventSlot, Attendees, Selections
    
    # Get attendee user
    attendee_user = authenticated_client_attendee._transport.app.dependency_overrides[
        list(authenticated_client_attendee._transport.app.dependency_overrides.keys())[0]
    ](None)
    
    attendee = Attendees(
        id=str(ULID()),
        user_id=attendee_user["id"],
        convention_id=str(ULID())
    )
    selection_id = str(ULID())
    
    selection = Selections(
        id=selection_id,
        attendee_id=attendee.id,
        event_id=str(ULID()),
        event_slot_id=str(ULID()),
        commitment_level="interested"
    )
    
    db_session.add_all([attendee, selection])
    db_session.commit()
    
    response = authenticated_client_attendee.delete(f"/attendees/selections/{selection_id}")
    assert response.status_code == 200
    
    # Verify it's deleted
    deleted_selection = db_session.query(Selections).filter(Selections.id == selection_id).first()
    assert deleted_selection is None


def test_commit_to_workshop_directly(authenticated_client_attendee, db_session):
    """Test committing to a workshop directly."""
    from models import Events, EventSlot, Attendees
    
    # Get attendee user
    attendee_user = authenticated_client_attendee._transport.app.dependency_overrides[
        list(authenticated_client_attendee._transport.app.dependency_overrides.keys())[0]
    ](None)
    
    attendee = Attendees(
        id=str(ULID()),
        user_id=attendee_user["id"],
        convention_id=str(ULID())
    )
    workshop_id = str(ULID())
    slot_id = str(ULID())
    
    workshop = Events(
        id=workshop_id,
        name="Direct Commit Workshop",
        description="Can commit directly",
        convention_id=attendee.convention_id,
        max_students=10
    )
    slot = EventSlot(
        id=slot_id,
        convention_id=attendee.convention_id,
        location_id=str(ULID()),
        start_time=datetime.now() + timedelta(days=1),
        end_time=datetime.now() + timedelta(days=1, hours=1),
        event_id=workshop_id,
        day_number=1
    )
    
    db_session.add_all([attendee, workshop, slot])
    db_session.commit()
    
    response = authenticated_client_attendee.post(
        f"/attendees/commit/{workshop_id}",
        params={"event_slot_id": slot_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["workshop"]["id"] == workshop_id
    assert data["commitment_level"] == "committed"


def test_get_my_schedule(authenticated_client_attendee, db_session):
    """Test getting own schedule as attendee."""
    from models import Events, EventSlot, Attendees, Selections, Users, Locations
    
    # Get attendee user
    attendee_user = authenticated_client_attendee._transport.app.dependency_overrides[
        list(authenticated_client_attendee._transport.app.dependency_overrides.keys())[0]
    ](None)
    
    attendee = Attendees(
        id=str(ULID()),
        user_id=attendee_user["id"],
        convention_id=str(ULID())
    )
    
    # Create user record
    user = Users(
        id=attendee_user["id"],
        email=attendee_user["email"],
        name=attendee_user["name"]
    )
    
    # Create workshops and selections
    workshop1 = Events(
        id=str(ULID()),
        name="Morning Workshop",
        description="Morning session",
        convention_id=attendee.convention_id,
        max_students=10
    )
    workshop2 = Events(
        id=str(ULID()),
        name="Afternoon Workshop",
        description="Afternoon session",
        convention_id=attendee.convention_id,
        max_students=10
    )
    
    location = Locations(
        id=str(ULID()),
        name="Main Hall",
        convention_id=attendee.convention_id
    )
    
    slot1 = EventSlot(
        id=str(ULID()),
        convention_id=attendee.convention_id,
        location_id=location.id,
        start_time=datetime.now() + timedelta(days=1, hours=9),
        end_time=datetime.now() + timedelta(days=1, hours=10),
        event_id=workshop1.id,
        day_number=1
    )
    slot2 = EventSlot(
        id=str(ULID()),
        convention_id=attendee.convention_id,
        location_id=location.id,
        start_time=datetime.now() + timedelta(days=1, hours=14),
        end_time=datetime.now() + timedelta(days=1, hours=15),
        event_id=workshop2.id,
        day_number=1
    )
    
    selection1 = Selections(
        id=str(ULID()),
        attendee_id=attendee.id,
        event_id=workshop1.id,
        event_slot_id=slot1.id,
        commitment_level="committed"
    )
    selection2 = Selections(
        id=str(ULID()),
        attendee_id=attendee.id,
        event_id=workshop2.id,
        event_slot_id=slot2.id,
        commitment_level="interested"
    )
    
    db_session.add_all([user, attendee, location, workshop1, workshop2, slot1, slot2, selection1, selection2])
    db_session.commit()
    
    response = authenticated_client_attendee.get("/attendees/schedule")
    assert response.status_code == 200
    data = response.json()
    assert data["attendee_id"] == attendee.id
    assert data["attendee_name"] == user.name
    assert len(data["selections"]) == 2
    assert data["committed_count"] == 1
    assert data["interested_count"] == 1
    assert data["maybe_count"] == 0


def test_get_other_attendee_schedule(test_client, db_session):
    """Test getting another attendee's schedule (public)."""
    from models import Attendees, Selections, Users
    
    attendee_id = str(ULID())
    user_id = str(ULID())
    
    user = Users(
        id=user_id,
        email="other@test.com",
        name="Other Attendee"
    )
    attendee = Attendees(
        id=attendee_id,
        user_id=user_id,
        convention_id=str(ULID())
    )
    selection = Selections(
        id=str(ULID()),
        attendee_id=attendee_id,
        event_id=str(ULID()),
        event_slot_id=str(ULID()),
        commitment_level="committed"
    )
    
    db_session.add_all([user, attendee, selection])
    db_session.commit()
    
    response = test_client.get(f"/attendees/{attendee_id}/schedule")
    assert response.status_code == 200
    data = response.json()
    assert data["attendee_id"] == attendee_id
    assert data["attendee_name"] == "Other Attendee"
    assert data["committed_count"] == 1


def test_filter_workshops_by_prerequisites(authenticated_client_attendee, db_session):
    """Test filtering workshops by prerequisites the attendee can fulfill."""
    from models import Events, Attendees, Selections, Capabilities
    
    # Get attendee user
    attendee_user = authenticated_client_attendee._transport.app.dependency_overrides[
        list(authenticated_client_attendee._transport.app.dependency_overrides.keys())[0]
    ](None)
    
    attendee = Attendees(
        id=str(ULID()),
        user_id=attendee_user["id"],
        convention_id=str(ULID())
    )
    
    # Create capabilities and workshops
    cap1_id = str(ULID())
    cap2_id = str(ULID())
    
    cap1 = Capabilities(id=cap1_id, name="Basic", description="Basic skill")
    cap2 = Capabilities(id=cap2_id, name="Advanced", description="Advanced skill")
    
    # Workshop with no prerequisites
    workshop1 = Events(
        id=str(ULID()),
        name="Beginner Workshop",
        description="No prerequisites",
        convention_id=attendee.convention_id,
        max_students=10,
        prerequisite_ids=[]
    )
    
    # Workshop with prerequisites
    workshop2 = Events(
        id=str(ULID()),
        name="Advanced Workshop",
        description="Requires skills",
        convention_id=attendee.convention_id,
        max_students=10,
        prerequisite_ids=[cap1_id, cap2_id]
    )
    
    db_session.add_all([attendee, cap1, cap2, workshop1, workshop2])
    db_session.commit()
    
    # Filter to only show workshops with prerequisites the attendee can fulfill
    response = authenticated_client_attendee.get("/attendees/workshops/filtered?max_fulfilled=true")
    assert response.status_code == 200
    data = response.json()
    
    # Should only show the beginner workshop since attendee has no completed workshops/capabilities
    assert len(data) == 1
    assert data[0]["id"] == workshop1.id