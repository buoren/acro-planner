"""
Tests for equipment management API endpoints.
"""

import pytest
from ulid import ULID


def test_create_equipment_admin_only(test_client, authenticated_client_admin, db_session):
    """Test that only admins can create equipment."""
    from models import Locations
    
    loc_id = str(ULID())
    location = Locations(
        id=loc_id,
        name="Main Hall",
        convention_id=str(ULID())
    )
    db_session.add(location)
    db_session.commit()
    
    equipment_data = {
        "name": "Yoga Mats",
        "description": "High-quality yoga mats",
        "location_id": loc_id,
        "quantity": 20
    }
    
    # Admin should succeed
    response = authenticated_client_admin.post("/equipment/", json=equipment_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Yoga Mats"
    assert data["quantity"] == 20
    assert data["location_id"] == loc_id
    
    # Non-admin should fail
    response = test_client.post("/equipment/", json=equipment_data)
    assert response.status_code == 401


def test_list_equipment_public(test_client, db_session):
    """Test that listing equipment is public."""
    from models import Equipment, Locations
    
    loc_id = str(ULID())
    conv_id = str(ULID())
    location = Locations(id=loc_id, name="Studio", convention_id=conv_id)
    
    equip1 = Equipment(
        id=str(ULID()),
        name="Blocks",
        quantity=30,
        location_id=loc_id,
        convention_id=conv_id
    )
    equip2 = Equipment(
        id=str(ULID()),
        name="Straps",
        quantity=15,
        location_id=loc_id,
        convention_id=conv_id
    )
    
    db_session.add_all([location, equip1, equip2])
    db_session.commit()
    
    # List all equipment
    response = test_client.get("/equipment/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    # Filter by location
    response = test_client.get(f"/equipment/?location_id={loc_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    # Filter by convention
    response = test_client.get(f"/equipment/?convention_id={conv_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_equipment_details(test_client, db_session):
    """Test getting equipment details."""
    from models import Equipment, Locations
    
    loc_id = str(ULID())
    equip_id = str(ULID())
    
    location = Locations(id=loc_id, name="Gym", convention_id=str(ULID()))
    equipment = Equipment(
        id=equip_id,
        name="Crash Mats",
        description="Safety mats for aerial work",
        quantity=5,
        location_id=loc_id,
        convention_id=location.convention_id
    )
    
    db_session.add_all([location, equipment])
    db_session.commit()
    
    response = test_client.get(f"/equipment/{equip_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == equip_id
    assert data["name"] == "Crash Mats"
    assert data["location_name"] == "Gym"


def test_update_equipment(authenticated_client_admin, db_session):
    """Test updating equipment details."""
    from models import Equipment, Locations
    
    loc_id = str(ULID())
    equip_id = str(ULID())
    
    location = Locations(id=loc_id, name="Studio", convention_id=str(ULID()))
    equipment = Equipment(
        id=equip_id,
        name="Old Name",
        quantity=10,
        location_id=loc_id,
        convention_id=location.convention_id
    )
    
    db_session.add_all([location, equipment])
    db_session.commit()
    
    update_data = {
        "name": "New Name",
        "description": "Updated description",
        "quantity": 15
    }
    
    response = authenticated_client_admin.put(f"/equipment/{equip_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["description"] == "Updated description"
    assert data["quantity"] == 15


def test_update_equipment_invalid_quantity(authenticated_client_admin, db_session):
    """Test that updating equipment with invalid quantity fails."""
    from models import Equipment
    
    equip_id = str(ULID())
    equipment = Equipment(
        id=equip_id,
        name="Test Equipment",
        quantity=5,
        location_id=str(ULID()),
        convention_id=str(ULID())
    )
    db_session.add(equipment)
    db_session.commit()
    
    update_data = {"quantity": 0}
    
    response = authenticated_client_admin.put(f"/equipment/{equip_id}", json=update_data)
    assert response.status_code == 400
    assert "at least 1" in response.json()["detail"].lower()


def test_delete_equipment(authenticated_client_admin, db_session):
    """Test deleting equipment."""
    from models import Equipment
    
    equip_id = str(ULID())
    equipment = Equipment(
        id=equip_id,
        name="Deletable",
        quantity=1,
        location_id=str(ULID()),
        convention_id=str(ULID())
    )
    db_session.add(equipment)
    db_session.commit()
    
    response = authenticated_client_admin.delete(f"/equipment/{equip_id}")
    assert response.status_code == 200
    
    # Verify it's deleted
    deleted = db_session.query(Equipment).filter(Equipment.id == equip_id).first()
    assert deleted is None


def test_add_equipment_to_location(authenticated_client_admin, db_session):
    """Test adding equipment directly to a specific location."""
    from models import Locations
    
    loc_id = str(ULID())
    location = Locations(
        id=loc_id,
        name="Practice Room",
        convention_id=str(ULID())
    )
    db_session.add(location)
    db_session.commit()
    
    equipment_data = {
        "name": "Speaker System",
        "description": "Bluetooth speaker for music",
        "quantity": 2,
        "location_id": "ignored"  # This should be overridden
    }
    
    response = authenticated_client_admin.post(
        f"/equipment/locations/{loc_id}/equipment",
        json=equipment_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["location_id"] == loc_id
    assert data["location_name"] == "Practice Room"


def test_list_location_equipment(test_client, db_session):
    """Test listing all equipment at a specific location."""
    from models import Equipment, Locations
    
    loc1_id = str(ULID())
    loc2_id = str(ULID())
    conv_id = str(ULID())
    
    loc1 = Locations(id=loc1_id, name="Room A", convention_id=conv_id)
    loc2 = Locations(id=loc2_id, name="Room B", convention_id=conv_id)
    
    # Equipment in Room A
    equip1 = Equipment(
        id=str(ULID()),
        name="Mats",
        quantity=10,
        location_id=loc1_id,
        convention_id=conv_id
    )
    equip2 = Equipment(
        id=str(ULID()),
        name="Blocks",
        quantity=20,
        location_id=loc1_id,
        convention_id=conv_id
    )
    
    # Equipment in Room B
    equip3 = Equipment(
        id=str(ULID()),
        name="Straps",
        quantity=15,
        location_id=loc2_id,
        convention_id=conv_id
    )
    
    db_session.add_all([loc1, loc2, equip1, equip2, equip3])
    db_session.commit()
    
    # Get equipment for Room A only
    response = test_client.get(f"/equipment/locations/{loc1_id}/equipment")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(e["location_id"] == loc1_id for e in data)


def test_equipment_location_not_found(authenticated_client_admin):
    """Test creating equipment with non-existent location fails."""
    equipment_data = {
        "name": "Test Equipment",
        "location_id": str(ULID()),  # Non-existent
        "quantity": 5
    }
    
    response = authenticated_client_admin.post("/equipment/", json=equipment_data)
    assert response.status_code == 404
    assert "location not found" in response.json()["detail"].lower()