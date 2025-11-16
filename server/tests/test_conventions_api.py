"""
Tests for convention management API endpoints.
"""

import pytest
from datetime import datetime, timedelta
from ulid import ULID


def test_create_convention_admin_only(test_client, test_user_admin, authenticated_client_admin):
    """Test that only admins can create conventions."""
    convention_data = {
        "name": "AcroYoga Convention 2024",
        "description": "Annual acro convention",
        "start_date": (datetime.now() + timedelta(days=30)).isoformat(),
        "end_date": (datetime.now() + timedelta(days=33)).isoformat(),
        "location_ids": []
    }
    
    # Admin should succeed
    response = authenticated_client_admin.post("/conventions/", json=convention_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == convention_data["name"]
    assert data["description"] == convention_data["description"]
    assert "id" in data
    
    # Non-admin should fail
    response = test_client.post("/conventions/", json=convention_data)
    assert response.status_code == 401


def test_list_conventions_public(test_client, db_session):
    """Test that listing conventions is public."""
    from models import Conventions
    from datetime import date
    
    # Create test conventions
    conv1 = Conventions(
        id=str(ULID()),
        name="Spring Convention",
        description="Spring gathering",
        start_date=date(2024, 3, 15),
        end_date=date(2024, 3, 18),
        is_active=True
    )
    conv2 = Conventions(
        id=str(ULID()),
        name="Fall Convention",
        description="Fall gathering",
        start_date=date(2024, 10, 15),
        end_date=date(2024, 10, 18),
        is_active=True
    )
    db_session.add_all([conv1, conv2])
    db_session.commit()
    
    # Public access should work
    response = test_client.get("/conventions/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(c["name"] == "Spring Convention" for c in data)
    assert any(c["name"] == "Fall Convention" for c in data)


def test_get_convention_details(test_client, db_session):
    """Test getting convention details."""
    from models import Conventions
    from datetime import date
    
    conv_id = str(ULID())
    convention = Conventions(
        id=conv_id,
        name="Test Convention",
        description="Test description",
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 3),
        is_active=True
    )
    db_session.add(convention)
    db_session.commit()
    
    response = test_client.get(f"/conventions/{conv_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == conv_id
    assert data["name"] == "Test Convention"
    assert data["description"] == "Test description"


def test_update_convention_admin_only(test_client, test_user_admin, authenticated_client_admin, db_session):
    """Test that only admins can update conventions."""
    from models import Conventions
    from datetime import date
    
    conv_id = str(ULID())
    convention = Conventions(
        id=conv_id,
        name="Original Name",
        description="Original description",
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 3),
        is_active=True
    )
    db_session.add(convention)
    db_session.commit()
    
    update_data = {
        "name": "Updated Name",
        "description": "Updated description"
    }
    
    # Admin should succeed
    response = authenticated_client_admin.put(f"/conventions/{conv_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "Updated description"
    
    # Non-admin should fail
    response = test_client.put(f"/conventions/{conv_id}", json=update_data)
    assert response.status_code == 401


def test_add_location_to_convention(authenticated_client_admin, db_session):
    """Test adding a location to a convention."""
    from models import Conventions
    from datetime import date
    
    conv_id = str(ULID())
    convention = Conventions(
        id=conv_id,
        name="Test Convention",
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 3),
        is_active=True
    )
    db_session.add(convention)
    db_session.commit()
    
    location_data = {
        "name": "Main Hall",
        "description": "Large practice space",
        "capacity": 100,
        "address": "123 Acro Street"
    }
    
    response = authenticated_client_admin.post(f"/conventions/{conv_id}/locations", json=location_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Main Hall"
    assert data["capacity"] == 100
    assert "id" in data


def test_create_event_slot(authenticated_client_admin, db_session):
    """Test creating an event slot for a convention."""
    from models import Conventions, Locations
    from datetime import date
    
    conv_id = str(ULID())
    loc_id = str(ULID())
    
    convention = Conventions(
        id=conv_id,
        name="Test Convention",
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 3),
        is_active=True
    )
    location = Locations(
        id=loc_id,
        name="Main Hall",
        convention_id=conv_id
    )
    db_session.add_all([convention, location])
    db_session.commit()
    
    slot_data = {
        "convention_id": conv_id,
        "location_id": loc_id,
        "start_time": datetime(2024, 6, 1, 10, 0).isoformat(),
        "end_time": datetime(2024, 6, 1, 11, 30).isoformat()
    }
    
    response = authenticated_client_admin.post(f"/conventions/{conv_id}/event-slots", json=slot_data)
    assert response.status_code == 200
    data = response.json()
    assert data["convention_id"] == conv_id
    assert data["location"]["id"] == loc_id
    assert "id" in data


def test_list_event_slots(test_client, db_session):
    """Test listing event slots for a convention."""
    from models import Conventions, Locations, EventSlot
    from datetime import date, datetime
    
    conv_id = str(ULID())
    loc_id = str(ULID())
    
    convention = Conventions(
        id=conv_id,
        name="Test Convention",
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 3),
        is_active=True
    )
    location = Locations(
        id=loc_id,
        name="Main Hall",
        convention_id=conv_id
    )
    slot1 = EventSlot(
        id=str(ULID()),
        convention_id=conv_id,
        location_id=loc_id,
        start_time=datetime(2024, 6, 1, 9, 0),
        end_time=datetime(2024, 6, 1, 10, 30),
        day_number=1
    )
    slot2 = EventSlot(
        id=str(ULID()),
        convention_id=conv_id,
        location_id=loc_id,
        start_time=datetime(2024, 6, 1, 11, 0),
        end_time=datetime(2024, 6, 1, 12, 30),
        day_number=1
    )
    db_session.add_all([convention, location, slot1, slot2])
    db_session.commit()
    
    response = test_client.get(f"/conventions/{conv_id}/event-slots")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_update_location(authenticated_client_admin, db_session):
    """Test updating location details."""
    from models import Locations
    
    loc_id = str(ULID())
    location = Locations(
        id=loc_id,
        name="Original Name",
        capacity=50,
        convention_id=str(ULID())
    )
    db_session.add(location)
    db_session.commit()
    
    update_data = {
        "name": "Updated Hall",
        "capacity": 75,
        "description": "Newly renovated space"
    }
    
    response = authenticated_client_admin.put(f"/conventions/locations/{loc_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Hall"
    assert data["capacity"] == 75
    assert data["description"] == "Newly renovated space"


def test_delete_convention(authenticated_client_admin, db_session):
    """Test deleting (deactivating) a convention."""
    from models import Conventions
    from datetime import date
    
    conv_id = str(ULID())
    convention = Conventions(
        id=conv_id,
        name="Test Convention",
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 3),
        is_active=True
    )
    db_session.add(convention)
    db_session.commit()
    
    response = authenticated_client_admin.delete(f"/conventions/{conv_id}")
    assert response.status_code == 200
    
    # Verify it's deactivated
    db_session.refresh(convention)
    assert convention.is_active == False


def test_delete_event_slot_with_event_fails(authenticated_client_admin, db_session):
    """Test that deleting an event slot with a scheduled event fails."""
    from models import EventSlot, Events
    
    slot_id = str(ULID())
    event_id = str(ULID())
    
    slot = EventSlot(
        id=slot_id,
        convention_id=str(ULID()),
        location_id=str(ULID()),
        start_time=datetime.now(),
        end_time=datetime.now() + timedelta(hours=1),
        event_id=event_id,
        day_number=1
    )
    db_session.add(slot)
    db_session.commit()
    
    response = authenticated_client_admin.delete(f"/conventions/event-slots/{slot_id}")
    assert response.status_code == 400
    assert "scheduled event" in response.json()["detail"].lower()