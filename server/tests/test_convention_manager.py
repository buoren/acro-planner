"""
Tests for ConventionManager functionality.
"""

import pytest
import ulid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from api.convention import ConventionManager
from models import Conventions, Locations, EventSlot, Events


class TestConventionManager:
    """Tests for ConventionManager class."""

    def test_add_location_for_convention_success(self, db_session):
        """Test adding a location to a convention."""
        # Create convention
        convention = Conventions(
            id=str(ulid.new()),
            name="Test Convention",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=3)
        )
        db_session.add(convention)
        db_session.commit()
        
        manager = ConventionManager(db_session)
        location = manager.add_location_for_convention(
            convention_id=convention.id,
            name="Main Hall",
            details={"capacity": 100},
            equipment_ids=["eq1", "eq2"]
        )
        
        assert location is not None
        assert location.name == "Main Hall"
        assert location.convention_id == convention.id
        assert location.details == {"capacity": 100}
        assert location.equipment_ids == ["eq1", "eq2"]

    def test_add_location_for_convention_nonexistent(self, db_session):
        """Test adding location to non-existent convention raises error."""
        manager = ConventionManager(db_session)
        
        with pytest.raises(ValueError, match="Convention.*does not exist"):
            manager.add_location_for_convention(
                convention_id="nonexistent-id",
                name="Main Hall",
                details={},
                equipment_ids=[]
            )

    def test_add_slots_for_convention_success(self, db_session):
        """Test adding slots for a convention."""
        # Create convention
        convention = Conventions(
            id=str(ulid.new()),
            name="Test Convention",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=3)
        )
        db_session.add(convention)
        db_session.commit()
        
        # Create locations
        location1 = Locations(
            id=str(ulid.new()),
            name="Location 1",
            details={},
            equipment_ids=[],
            convention_id=convention.id
        )
        location2 = Locations(
            id=str(ulid.new()),
            name="Location 2",
            details={},
            equipment_ids=[],
            convention_id=convention.id
        )
        db_session.add_all([location1, location2])
        db_session.commit()
        
        # Define time slots
        base_time = datetime.now()
        time_slots = [
            (base_time, base_time + timedelta(hours=1)),
            (base_time + timedelta(hours=2), base_time + timedelta(hours=3))
        ]
        
        manager = ConventionManager(db_session)
        slots = manager.add_slots_for_convention(
            convention_id=convention.id,
            number_of_days=2,
            time_slots=time_slots,
            locations=[location1, location2]
        )
        
        # Should create 2 days * 2 time slots * 2 locations = 8 slots
        assert len(slots) == 8
        
        # Verify slot properties
        for slot in slots:
            assert slot.location_id in [location1.id, location2.id]
            assert slot.day_number in [1, 2]
            assert slot.start_time in [ts[0] for ts in time_slots]
            assert slot.end_time in [ts[1] for ts in time_slots]
            assert slot.event_id is None  # Slots start empty

    def test_add_slots_for_convention_nonexistent(self, db_session):
        """Test adding slots for non-existent convention raises error."""
        manager = ConventionManager(db_session)
        
        with pytest.raises(ValueError, match="Convention.*does not exist"):
            manager.add_slots_for_convention(
                convention_id="nonexistent-id",
                number_of_days=1,
                time_slots=[],
                locations=[]
            )

    def test_add_slots_for_convention_wrong_location(self, db_session):
        """Test adding slots with location from different convention raises error."""
        # Create conventions
        convention1 = Conventions(
            id=str(ulid.new()),
            name="Convention 1",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=3)
        )
        convention2 = Conventions(
            id=str(ulid.new()),
            name="Convention 2",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=3)
        )
        db_session.add_all([convention1, convention2])
        db_session.commit()
        
        # Create location for convention2
        location = Locations(
            id=str(ulid.new()),
            name="Location",
            details={},
            equipment_ids=[],
            convention_id=convention2.id
        )
        db_session.add(location)
        db_session.commit()
        
        manager = ConventionManager(db_session)
        base_time = datetime.now()
        time_slots = [(base_time, base_time + timedelta(hours=1))]
        
        with pytest.raises(ValueError, match="Location.*does not belong to convention"):
            manager.add_slots_for_convention(
                convention_id=convention1.id,
                number_of_days=1,
                time_slots=time_slots,
                locations=[location]
            )

    def test_delete_slot_success(self, db_session):
        """Test deleting an empty slot."""
        # Create convention
        convention = Conventions(
            id=str(ulid.new()),
            name="Test Convention",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=3)
        )
        db_session.add(convention)
        db_session.commit()
        
        # Create location
        location = Locations(
            id=str(ulid.new()),
            name="Location",
            details={},
            equipment_ids=[],
            convention_id=convention.id
        )
        db_session.add(location)
        db_session.commit()
        
        # Create empty slot
        slot = EventSlot(
            id=str(ulid.new()),
            location_id=location.id,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            event_id=None,  # Empty slot
            day_number=1
        )
        db_session.add(slot)
        db_session.commit()
        
        manager = ConventionManager(db_session)
        manager.delete_slot(slot.id)
        
        # Verify slot is deleted
        deleted_slot = db_session.query(EventSlot).filter(EventSlot.id == slot.id).first()
        assert deleted_slot is None

    def test_delete_slot_nonexistent(self, db_session):
        """Test deleting non-existent slot raises error."""
        manager = ConventionManager(db_session)
        
        with pytest.raises(ValueError, match="Slot.*does not exist"):
            manager.delete_slot("nonexistent-id")

    def test_delete_slot_not_empty(self, db_session):
        """Test deleting a slot with an event raises error."""
        # Create convention
        convention = Conventions(
            id=str(ulid.new()),
            name="Test Convention",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=3)
        )
        db_session.add(convention)
        db_session.commit()
        
        # Create event
        event = Events(
            id=str(ulid.new()),
            convention_id=convention.id,
            name="Test Event",
            description="Test Description",
            prerequisite_ids=[]
        )
        db_session.add(event)
        db_session.commit()
        
        # Create location
        location = Locations(
            id=str(ulid.new()),
            name="Location",
            details={},
            equipment_ids=[],
            convention_id=convention.id
        )
        db_session.add(location)
        db_session.commit()
        
        # Create slot with event
        slot = EventSlot(
            id=str(ulid.new()),
            location_id=location.id,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            event_id=event.id,  # Slot has event
            day_number=1
        )
        db_session.add(slot)
        db_session.commit()
        
        manager = ConventionManager(db_session)
        
        with pytest.raises(ValueError, match="Slot.*is not empty"):
            manager.delete_slot(slot.id)
        
        # Verify slot still exists
        existing_slot = db_session.query(EventSlot).filter(EventSlot.id == slot.id).first()
        assert existing_slot is not None

    def test_get_convention_from_id_success(self, db_session):
        """Test getting convention by ID."""
        convention = Conventions(
            id=str(ulid.new()),
            name="Test Convention",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=3)
        )
        db_session.add(convention)
        db_session.commit()
        
        manager = ConventionManager(db_session)
        result = manager.get_convention_from_id(convention.id)
        
        assert result is not None
        assert result.id == convention.id
        assert result.name == "Test Convention"

    def test_get_convention_from_id_not_found(self, db_session):
        """Test getting non-existent convention returns None."""
        manager = ConventionManager(db_session)
        result = manager.get_convention_from_id("nonexistent-id")
        
        assert result is None

    def test_get_slot_from_id_success(self, db_session):
        """Test getting slot by ID."""
        # Create convention
        convention = Conventions(
            id=str(ulid.new()),
            name="Test Convention",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=3)
        )
        db_session.add(convention)
        db_session.commit()
        
        # Create location
        location = Locations(
            id=str(ulid.new()),
            name="Location",
            details={},
            equipment_ids=[],
            convention_id=convention.id
        )
        db_session.add(location)
        db_session.commit()
        
        # Create slot
        slot = EventSlot(
            id=str(ulid.new()),
            location_id=location.id,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            event_id=None,
            day_number=1
        )
        db_session.add(slot)
        db_session.commit()
        
        manager = ConventionManager(db_session)
        result = manager.get_slot_from_id(slot.id)
        
        assert result is not None
        assert result.id == slot.id
        assert result.location_id == location.id

    def test_get_slot_from_id_not_found(self, db_session):
        """Test getting non-existent slot returns None."""
        manager = ConventionManager(db_session)
        result = manager.get_slot_from_id("nonexistent-id")
        
        assert result is None

