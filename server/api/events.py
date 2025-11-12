"""
File for event-related functionality.  EventSlot handling is here as well.
"""

import ulid
from sqlalchemy.orm import Session
from typing import Optional, List
from models import Events, Selections, EventSlot
from datetime import datetime

class EventsManager:
    def __init__(self, db: Session):
        self.db = db

    def get_event_from_id(self, event_id: str) -> Optional[Events]:
        """
        Get event record from ID.
        
        Args:
            event_id: Event ID to get
            
        Returns:
            Events record if found, None otherwise
        """
        events = self.db.query(Events).filter(Events.id == event_id).all()
        if len(events) != 1:
            raise ValueError(f"Expected exactly 1 event for ID {event_id}, but got {len(events)}")
        return events[0]

    def get_events_from_convention_id(self, convention_id: str) -> List[Events]:
        """
        Get all events for a convention.
        
        Args:
            convention_id: Convention ID to get events for
            
        Returns:
            List of Events records if found, empty list otherwise
        """
        return self.db.query(Events).filter(Events.convention_id == convention_id).all()

    def get_events_for_day_number(self, convention_id: str, day_number: int) -> List[Events]:
        """
        Get all events for a day number (via event slots).
        
        Args:
            convention_id: Convention ID to get events for
            day_number: Day number to get events for
            
        Returns:
            List of Events records if found, empty list otherwise
        """
        slots = self.db.query(EventSlot).filter(EventSlot.day_number == day_number).all()
        event_ids = {slot.event_id for slot in slots if slot.event_id is not None}
        if not event_ids:
            return []
        return self.db.query(Events).filter(Events.id.in_(event_ids), Events.convention_id == convention_id).all()

    def get_events_by_prerequisites(self, prerequisite_ids: List[str]) -> List[Events]:
        """
        Get all events by prerequisites.
        
        Args:
            prerequisite_ids: List of prerequisite IDs to get events for
            
        Returns:
            List of Events records if found, empty list otherwise
        """
        return self.db.query(Events).filter(Events.prerequisite_ids.contains(prerequisite_ids)).all()

    def get_event_interest_count(self, event_id: str) -> int:
        """
        Get the number of times an event has been selected.
        
        Args:
            event_id: Event ID to get interest count for
            
        Returns:
            Number of times an event has been selected
        """
        return self.db.query(Selections).filter(Selections.event_id == event_id).count()

    def get_event_registration_count(self, event_id: str) -> int:
        """
        Get the number of times an event has been registered.
        
        Args:
            event_id: Event ID to get registration count for
            
        Returns:
            Number of times an event has been registered
        """
        return self.db.query(Selections).filter(Selections.event_id == event_id, Selections.is_selected == True).count()

    def get_events_by_location_id(self, location_id: str) -> List[Events]:
        """
        Get all events by location ID (via event slots).
        
        Args:
            location_id: Location ID to get events for
            
        Returns:
            List of Events records if found, empty list otherwise
        """
        slots = self.db.query(EventSlot).filter(EventSlot.location_id == location_id).all()
        event_ids = {slot.event_id for slot in slots if slot.event_id is not None}
        if not event_ids:
            return []
        return self.db.query(Events).filter(Events.id.in_(event_ids)).all()

    def create_new_event(self, name: str, description: str, prerequisite_ids: List[str], convention_id: str) -> Events:
        """
        Create a new event.
        
        Args:
            name: Event name
            description: Event description
            prerequisite_ids: List of prerequisite capability IDs
            convention_id: Convention ID this event belongs to
            
        Returns:
            Events record if created, None otherwise
        """
        event = Events(
            id=str(ulid.new()),
            name=name,
            description=description,
            prerequisite_ids=prerequisite_ids,
            convention_id=convention_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_planned_event_for_slot(self, slot_id: str) -> Optional[Events]:
        """
        Get the event for a slot.
        
        Args:
            slot_id: Slot ID to get event for
            
        Returns:
            Events record if found, None otherwise
        """
        slot = self.get_event_slot_from_id(slot_id)
        if not slot or slot.event_id is None:
            return None
        return self.get_event_from_id(slot.event_id)

    def get_events_by_slot_id(self, slot_id: str) -> List[Events]:
        """
        Get all events by slot ID.
        
        Args:
            slot_id: Slot ID to get events for
            
        Returns:
            List of Events records if found, empty list otherwise
        """
        slot = self.get_event_slot_from_id(slot_id)
        if not slot or slot.event_id is None:
            return []
        event = self.get_event_from_id(slot.event_id)
        return [event] if event else []

    def assign_event_to_slot(self, event_id: str, slot_id: str) -> Optional[Events]:
        """
        Assign an event to a slot.
        
        Args:
            event_id: Event ID to assign to slot
            slot_id: Slot ID to assign event to
            
        Returns:
            Events record if another event was unassigned, None otherwise
        """
        event = self.get_event_from_id(event_id)
        if not event:
            raise ValueError(f"Event {event_id} does not exist")
        slot = self.get_event_slot_from_id(slot_id)
        if not slot:
            raise ValueError(f"Slot {slot_id} does not exist")
        old_event = None
        if slot.event_id is not None and slot.event_id != event_id:
            old_event_id = slot.event_id
            old_event = self.get_event_from_id(old_event_id)
            if not old_event:
                raise ValueError(f"Event {old_event_id} does not exist")
        slot.event_id = event_id
        self.db.commit()
        self.db.refresh(slot)
        return old_event

    def get_event_slot_from_id(self, slot_id: str) -> Optional[EventSlot]:
        """
        Get event slot record from ID.
        
        Args:
            slot_id: Slot ID to get
            
        Returns:
            EventSlot record if found, None otherwise
        """
        slots = self.db.query(EventSlot).filter(EventSlot.id == slot_id).all()
        if len(slots) != 1:
            raise ValueError(f"Expected exactly 1 slot for ID {slot_id}, but got {len(slots)}")
        return slots[0]
