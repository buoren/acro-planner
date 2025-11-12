"""
Tests for EventsManager functionality.
"""

import pytest
import ulid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from api.events import EventsManager
from models import Events, EventSlot, Conventions, Locations


class TestEventsManager:
    """Tests for EventsManager class."""

    def test_get_event_from_id_success(self, db_session):
        """Test getting an event by ID."""
        # Create a convention first
        convention = Conventions(
            id=str(ulid.new()),
            name="Test Convention",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=3)
        )
        db_session.add(convention)
        db_session.commit()
        
        # Create an event
        event = Events(
            id=str(ulid.new()),
            convention_id=convention.id,
            name="Test Event",
            description="Test Description",
            prerequisite_ids=[]
        )
        db_session.add(event)
        db_session.commit()
        
        manager = EventsManager(db_session)
        result = manager.get_event_from_id(event.id)
        
        assert result is not None
        assert result.id == event.id
        assert result.name == "Test Event"

    def test_get_event_from_id_not_found(self, db_session):
        """Test getting a non-existent event raises error."""
        manager = EventsManager(db_session)
        
        with pytest.raises(ValueError, match="Expected exactly 1 event"):
            manager.get_event_from_id("nonexistent-id")

    def test_get_events_from_convention_id(self, db_session):
        """Test getting events for a convention."""
        # Create convention
        convention = Conventions(
            id=str(ulid.new()),
            name="Test Convention",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=3)
        )
        db_session.add(convention)
        db_session.commit()
        
        # Create events
        event1 = Events(
            id=str(ulid.new()),
            convention_id=convention.id,
            name="Event 1",
            description="Description 1",
            prerequisite_ids=[]
        )
        event2 = Events(
            id=str(ulid.new()),
            convention_id=convention.id,
            name="Event 2",
            description="Description 2",
            prerequisite_ids=[]
        )
        db_session.add_all([event1, event2])
        db_session.commit()
        
        manager = EventsManager(db_session)
        results = manager.get_events_from_convention_id(convention.id)
        
        assert len(results) == 2
        assert {r.id for r in results} == {event1.id, event2.id}

    def test_get_event_slot_from_id_success(self, db_session):
        """Test getting an event slot by ID."""
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
            name="Test Location",
            details={},
            equipment_ids=[],
            convention_id=convention.id
        )
        db_session.add(location)
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
        
        # Create event slot
        slot = EventSlot(
            id=str(ulid.new()),
            location_id=location.id,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            event_id=event.id,
            day_number=1
        )
        db_session.add(slot)
        db_session.commit()
        
        manager = EventsManager(db_session)
        result = manager.get_event_slot_from_id(slot.id)
        
        assert result is not None
        assert result.id == slot.id
        assert result.event_id == event.id
        assert result.location_id == location.id

    def test_get_event_slot_from_id_not_found(self, db_session):
        """Test getting a non-existent slot raises error."""
        manager = EventsManager(db_session)
        
        with pytest.raises(ValueError, match="Expected exactly 1 slot"):
            manager.get_event_slot_from_id("nonexistent-id")

    def test_get_planned_event_for_slot(self, db_session):
        """Test getting the event for a slot."""
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
            name="Test Location",
            details={},
            equipment_ids=[],
            convention_id=convention.id
        )
        db_session.add(location)
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
        
        # Create event slot
        slot = EventSlot(
            id=str(ulid.new()),
            location_id=location.id,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            event_id=event.id,
            day_number=1
        )
        db_session.add(slot)
        db_session.commit()
        
        manager = EventsManager(db_session)
        result = manager.get_planned_event_for_slot(slot.id)
        
        assert result is not None
        assert result.id == event.id
        assert result.name == "Test Event"

    def test_get_events_by_slot_id(self, db_session):
        """Test getting events by slot ID."""
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
            name="Test Location",
            details={},
            equipment_ids=[],
            convention_id=convention.id
        )
        db_session.add(location)
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
        
        # Create event slot
        slot = EventSlot(
            id=str(ulid.new()),
            location_id=location.id,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            event_id=event.id,
            day_number=1
        )
        db_session.add(slot)
        db_session.commit()
        
        manager = EventsManager(db_session)
        results = manager.get_events_by_slot_id(slot.id)
        
        assert len(results) == 1
        assert results[0].id == event.id

    def test_assign_event_to_slot(self, db_session):
        """Test assigning an event to a slot."""
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
            name="Test Location",
            details={},
            equipment_ids=[],
            convention_id=convention.id
        )
        db_session.add(location)
        db_session.commit()
        
        # Create events
        event1 = Events(
            id=str(ulid.new()),
            convention_id=convention.id,
            name="Event 1",
            description="Description 1",
            prerequisite_ids=[]
        )
        event2 = Events(
            id=str(ulid.new()),
            convention_id=convention.id,
            name="Event 2",
            description="Description 2",
            prerequisite_ids=[]
        )
        db_session.add_all([event1, event2])
        db_session.commit()
        
        # Create event slot with event1
        slot = EventSlot(
            id=str(ulid.new()),
            location_id=location.id,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            event_id=event1.id,
            day_number=1
        )
        db_session.add(slot)
        db_session.commit()
        
        manager = EventsManager(db_session)
        old_event = manager.assign_event_to_slot(event2.id, slot.id)
        
        # Should return the old event (event1)
        assert old_event is not None
        assert old_event.id == event1.id
        
        # Slot should now have event2
        db_session.refresh(slot)
        assert slot.event_id == event2.id

    def test_assign_event_to_slot_no_previous_event(self, db_session):
        """Test assigning an event to an empty slot."""
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
            name="Test Location",
            details={},
            equipment_ids=[],
            convention_id=convention.id
        )
        db_session.add(location)
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
        
        # Create event slot (this will have event_id set, but we'll reassign)
        slot = EventSlot(
            id=str(ulid.new()),
            location_id=location.id,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            event_id=event.id,
            day_number=1
        )
        db_session.add(slot)
        db_session.commit()
        
        # Create new event
        new_event = Events(
            id=str(ulid.new()),
            convention_id=convention.id,
            name="New Event",
            description="New Description",
            prerequisite_ids=[]
        )
        db_session.add(new_event)
        db_session.commit()
        
        manager = EventsManager(db_session)
        old_event = manager.assign_event_to_slot(new_event.id, slot.id)
        
        # Should return the old event
        assert old_event is not None
        assert old_event.id == event.id
        
        # Slot should now have new_event
        db_session.refresh(slot)
        assert slot.event_id == new_event.id

    def test_get_events_by_location_id(self, db_session):
        """Test getting events by location ID."""
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
        
        # Create events
        event1 = Events(
            id=str(ulid.new()),
            convention_id=convention.id,
            name="Event 1",
            description="Description 1",
            prerequisite_ids=[]
        )
        event2 = Events(
            id=str(ulid.new()),
            convention_id=convention.id,
            name="Event 2",
            description="Description 2",
            prerequisite_ids=[]
        )
        db_session.add_all([event1, event2])
        db_session.commit()
        
        # Create event slots
        slot1 = EventSlot(
            id=str(ulid.new()),
            location_id=location1.id,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            event_id=event1.id,
            day_number=1
        )
        slot2 = EventSlot(
            id=str(ulid.new()),
            location_id=location1.id,
            start_time=datetime.now() + timedelta(hours=2),
            end_time=datetime.now() + timedelta(hours=3),
            event_id=event2.id,
            day_number=1
        )
        slot3 = EventSlot(
            id=str(ulid.new()),
            location_id=location2.id,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            event_id=event1.id,
            day_number=1
        )
        db_session.add_all([slot1, slot2, slot3])
        db_session.commit()
        
        manager = EventsManager(db_session)
        results = manager.get_events_by_location_id(location1.id)
        
        # Should return both events that have slots at location1
        assert len(results) == 2
        assert {r.id for r in results} == {event1.id, event2.id}

    def test_get_events_for_day_number(self, db_session):
        """Test getting events for a day number."""
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
            name="Test Location",
            details={},
            equipment_ids=[],
            convention_id=convention.id
        )
        db_session.add(location)
        db_session.commit()
        
        # Create events
        event1 = Events(
            id=str(ulid.new()),
            convention_id=convention.id,
            name="Event 1",
            description="Description 1",
            prerequisite_ids=[]
        )
        event2 = Events(
            id=str(ulid.new()),
            convention_id=convention.id,
            name="Event 2",
            description="Description 2",
            prerequisite_ids=[]
        )
        db_session.add_all([event1, event2])
        db_session.commit()
        
        # Create event slots for different days
        slot1 = EventSlot(
            id=str(ulid.new()),
            location_id=location.id,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            event_id=event1.id,
            day_number=1
        )
        slot2 = EventSlot(
            id=str(ulid.new()),
            location_id=location.id,
            start_time=datetime.now() + timedelta(hours=2),
            end_time=datetime.now() + timedelta(hours=3),
            event_id=event2.id,
            day_number=1
        )
        slot3 = EventSlot(
            id=str(ulid.new()),
            location_id=location.id,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            event_id=event1.id,
            day_number=2
        )
        db_session.add_all([slot1, slot2, slot3])
        db_session.commit()
        
        manager = EventsManager(db_session)
        results = manager.get_events_for_day_number(convention.id, 1)
        
        # Should return both events that have slots on day 1
        assert len(results) == 2
        assert {r.id for r in results} == {event1.id, event2.id}

    def test_get_event_interest_count(self, db_session):
        """Test getting event interest count."""
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
        
        # Create selections (interest)
        from models import Selections, Attendees
        attendee = Attendees(
            id=str(ulid.new()),
            user_id=str(ulid.new()),
            convention_id=convention.id,
            is_registered=False
        )
        db_session.add(attendee)
        db_session.commit()
        
        selection1 = Selections(
            id=str(ulid.new()),
            attendee_id=attendee.id,
            event_id=event.id,
            is_selected=False
        )
        selection2 = Selections(
            id=str(ulid.new()),
            attendee_id=attendee.id,
            event_id=event.id,
            is_selected=False
        )
        db_session.add_all([selection1, selection2])
        db_session.commit()
        
        manager = EventsManager(db_session)
        count = manager.get_event_interest_count(event.id)
        
        assert count == 2

    def test_get_event_registration_count(self, db_session):
        """Test getting event registration count."""
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
        
        # Create selections
        from models import Selections, Attendees
        attendee = Attendees(
            id=str(ulid.new()),
            user_id=str(ulid.new()),
            convention_id=convention.id,
            is_registered=False
        )
        db_session.add(attendee)
        db_session.commit()
        
        # One selected (registered), one not selected (just interest)
        selection1 = Selections(
            id=str(ulid.new()),
            attendee_id=attendee.id,
            event_id=event.id,
            is_selected=True
        )
        selection2 = Selections(
            id=str(ulid.new()),
            attendee_id=attendee.id,
            event_id=event.id,
            is_selected=False
        )
        db_session.add_all([selection1, selection2])
        db_session.commit()
        
        manager = EventsManager(db_session)
        count = manager.get_event_registration_count(event.id)
        
        assert count == 1

    def test_create_new_event(self, db_session):
        """Test creating a new event."""
        # Create convention
        convention = Conventions(
            id=str(ulid.new()),
            name="Test Convention",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=3)
        )
        db_session.add(convention)
        db_session.commit()
        
        manager = EventsManager(db_session)
        event = manager.create_new_event(
            name="New Event",
            description="New Description",
            prerequisite_ids=["cap1", "cap2"],
            convention_id=convention.id
        )
        
        assert event is not None
        assert event.name == "New Event"
        assert event.description == "New Description"
        assert event.prerequisite_ids == ["cap1", "cap2"]
        assert event.convention_id == convention.id

