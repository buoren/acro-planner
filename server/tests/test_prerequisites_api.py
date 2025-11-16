"""
Tests for prerequisite management API endpoints.
"""

import pytest
from ulid import ULID


def test_create_prerequisite_admin_only(test_client, authenticated_client_admin):
    """Test that only admins can create prerequisites."""
    prereq_data = {
        "name": "L-Base",
        "description": "Basic L-basing skills",
        "parent_prerequisite_ids": []
    }
    
    # Admin should succeed
    response = authenticated_client_admin.post("/prerequisites/", json=prereq_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "L-Base"
    assert data["description"] == "Basic L-basing skills"
    assert "id" in data
    
    # Non-admin should fail
    response = test_client.post("/prerequisites/", json=prereq_data)
    assert response.status_code == 401


def test_create_prerequisite_with_parents(authenticated_client_admin, db_session):
    """Test creating a prerequisite with parent prerequisites (chaining)."""
    from models import Capabilities
    
    # Create parent prerequisites
    parent1_id = str(ULID())
    parent2_id = str(ULID())
    
    parent1 = Capabilities(
        id=parent1_id,
        name="Basic Trust",
        description="Basic trust and communication"
    )
    parent2 = Capabilities(
        id=parent2_id,
        name="Core Strength",
        description="Core strength requirements"
    )
    db_session.add_all([parent1, parent2])
    db_session.commit()
    
    # Create child prerequisite
    child_data = {
        "name": "Intermediate Flying",
        "description": "Intermediate flying skills",
        "parent_prerequisite_ids": [parent1_id, parent2_id]
    }
    
    response = authenticated_client_admin.post("/prerequisites/", json=child_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Intermediate Flying"
    assert len(data["parent_prerequisites"]) == 2
    assert len(data["all_prerequisites"]) == 2


def test_list_prerequisites_public(test_client, db_session):
    """Test that listing prerequisites is public."""
    from models import Capabilities
    
    cap1 = Capabilities(
        id=str(ULID()),
        name="Balance",
        description="Basic balance skills"
    )
    cap2 = Capabilities(
        id=str(ULID()),
        name="Flexibility",
        description="Basic flexibility"
    )
    db_session.add_all([cap1, cap2])
    db_session.commit()
    
    response = test_client.get("/prerequisites/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(p["name"] == "Balance" for p in data)
    assert any(p["name"] == "Flexibility" for p in data)


def test_get_prerequisite_details(test_client, db_session):
    """Test getting prerequisite details with all transitive prerequisites."""
    from models import Capabilities
    
    # Create prerequisite chain: A -> B -> C
    c_id = str(ULID())
    b_id = str(ULID())
    a_id = str(ULID())
    
    c = Capabilities(id=c_id, name="C", description="Prerequisite C")
    b = Capabilities(id=b_id, name="B", description="Prerequisite B", parent_capability_ids=[c_id])
    a = Capabilities(id=a_id, name="A", description="Prerequisite A", parent_capability_ids=[b_id])
    
    db_session.add_all([c, b, a])
    db_session.commit()
    
    response = test_client.get(f"/prerequisites/{a_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "A"
    assert len(data["parent_prerequisites"]) == 1  # Direct parent: B
    assert len(data["all_prerequisites"]) == 2  # All prerequisites: B and C


def test_update_prerequisite_admin_only(authenticated_client_admin, db_session):
    """Test that only admins can update prerequisites."""
    from models import Capabilities
    
    prereq_id = str(ULID())
    prereq = Capabilities(
        id=prereq_id,
        name="Original",
        description="Original description"
    )
    db_session.add(prereq)
    db_session.commit()
    
    update_data = {
        "name": "Updated",
        "description": "Updated description"
    }
    
    response = authenticated_client_admin.put(f"/prerequisites/{prereq_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"
    assert data["description"] == "Updated description"


def test_circular_dependency_prevention(authenticated_client_admin, db_session):
    """Test that circular dependencies are prevented."""
    from models import Capabilities
    
    # Create two prerequisites
    a_id = str(ULID())
    b_id = str(ULID())
    
    a = Capabilities(id=a_id, name="A", description="Prerequisite A")
    b = Capabilities(id=b_id, name="B", description="Prerequisite B", parent_capability_ids=[a_id])
    
    db_session.add_all([a, b])
    db_session.commit()
    
    # Try to make A depend on B (would create cycle)
    update_data = {
        "parent_prerequisite_ids": [b_id]
    }
    
    response = authenticated_client_admin.put(f"/prerequisites/{a_id}", json=update_data)
    assert response.status_code == 400
    assert "circular dependency" in response.json()["detail"].lower()


def test_self_dependency_prevention(authenticated_client_admin, db_session):
    """Test that a prerequisite cannot depend on itself."""
    from models import Capabilities
    
    prereq_id = str(ULID())
    prereq = Capabilities(
        id=prereq_id,
        name="Self",
        description="Test prerequisite"
    )
    db_session.add(prereq)
    db_session.commit()
    
    update_data = {
        "parent_prerequisite_ids": [prereq_id]
    }
    
    response = authenticated_client_admin.put(f"/prerequisites/{prereq_id}", json=update_data)
    assert response.status_code == 400
    assert "cannot depend on itself" in response.json()["detail"].lower()


def test_delete_prerequisite_with_dependents_fails(authenticated_client_admin, db_session):
    """Test that deleting a prerequisite that others depend on fails."""
    from models import Capabilities
    
    parent_id = str(ULID())
    child_id = str(ULID())
    
    parent = Capabilities(id=parent_id, name="Parent", description="Parent prerequisite")
    child = Capabilities(
        id=child_id,
        name="Child",
        description="Child prerequisite",
        parent_capability_ids=[parent_id]
    )
    
    db_session.add_all([parent, child])
    db_session.commit()
    
    # Try to delete parent (should fail)
    response = authenticated_client_admin.delete(f"/prerequisites/{parent_id}")
    assert response.status_code == 400
    assert "depend on" in response.json()["detail"].lower()


def test_delete_prerequisite_success(authenticated_client_admin, db_session):
    """Test successful prerequisite deletion."""
    from models import Capabilities
    
    prereq_id = str(ULID())
    prereq = Capabilities(
        id=prereq_id,
        name="Deletable",
        description="Can be deleted"
    )
    db_session.add(prereq)
    db_session.commit()
    
    response = authenticated_client_admin.delete(f"/prerequisites/{prereq_id}")
    assert response.status_code == 200
    
    # Verify it's deleted
    deleted = db_session.query(Capabilities).filter(Capabilities.id == prereq_id).first()
    assert deleted is None


def test_add_parent_prerequisite_host_allowed(authenticated_client_host, db_session):
    """Test that hosts can add parent prerequisites."""
    from models import Capabilities
    
    prereq_id = str(ULID())
    parent_id = str(ULID())
    
    prereq = Capabilities(id=prereq_id, name="Child", description="Child prerequisite")
    parent = Capabilities(id=parent_id, name="Parent", description="Parent prerequisite")
    
    db_session.add_all([prereq, parent])
    db_session.commit()
    
    response = authenticated_client_host.post(
        f"/prerequisites/{prereq_id}/add-parent",
        params={"parent_id": parent_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["parent_prerequisites"]) == 1
    assert any(p["id"] == parent_id for p in data["parent_prerequisites"])