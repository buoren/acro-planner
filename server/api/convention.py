"""
Configuring a convention happens here.
"""

import ulid
from sqlalchemy.orm import Session
from typing import Optional, List, Tuple
from models import Conventions, Events, EventSlot, Locations
from datetime import datetime

class ConventionManager:
    def __init__(self, db: Session):
        self.db = db

    def get_convention_from_id(self, convention_id: str) -> Optional[Conventions]:
        """
        Get convention record from ID.
        
        Args:
            convention_id: Convention ID to get
            
        Returns:
            Conventions record if found, None otherwise
        """
        conventions = self.db.query(Conventions).filter(Conventions.id == convention_id).all()
        if len(conventions) != 1:
            return None
        return conventions[0]

    def get_slot_from_id(self, slot_id: str) -> Optional[EventSlot]:
        """
        Get event slot record from ID.
        
        Args:
            slot_id: Slot ID to get
            
        Returns:
            EventSlot record if found, None otherwise
        """
        slots = self.db.query(EventSlot).filter(EventSlot.id == slot_id).all()
        if len(slots) != 1:
            return None
        return slots[0]

    def add_location_for_convention(self, convention_id: str, name: str, details: dict, equipment_ids: List[str]) -> Locations:
        """
        Add a location for a convention.
        
        Args:
            convention_id: Convention ID to add location for
            name: Name of the location
            details: Details of the location
            equipment_ids: List of equipment IDs for the location

        Returns:
            Locations record if added, None otherwise
        """
        convention = self.get_convention_from_id(convention_id)
        if not convention:
            raise ValueError(f"Convention {convention_id} does not exist")
        location = Locations(
            id=str(ulid.new()),
            name=name,
            details=details,
            equipment_ids=equipment_ids,
            convention_id=convention_id
        )
        self.db.add(location)
        self.db.commit()
        self.db.refresh(location)
        return location

    def add_slots_for_convention(self, convention_id: str, number_of_days: int, time_slots: List[Tuple[datetime, datetime]], locations: List[Locations]) -> List[EventSlot]:
        """
        Add slots for a convention.
        
        Args:
            convention_id: Convention ID to add slots for
            number_of_days: Number of days to add slots for
            time_slots: List of time slots to add
            locations: List of locations to add slots for

        Returns:
            List of EventSlot records if added, empty list otherwise
        """
        convention = self.get_convention_from_id(convention_id)
        if not convention:
            raise ValueError(f"Convention {convention_id} does not exist")
        for location in locations:
            if location.convention_id != convention_id:
                raise ValueError(f"Location {location.id} does not belong to convention {convention_id}")
        slots = []
        for day_number in range(1, number_of_days + 1):
            for time_slot in time_slots:
                for location in locations:
                    slot = EventSlot(
                        id=str(ulid.new()),
                        convention_id=convention_id,
                        location_id=location.id,
                        start_time=time_slot[0],
                        end_time=time_slot[1],
                        event_id=None,
                        day_number=day_number
                    )
                    self.db.add(slot)
                    slots.append(slot)
        self.db.commit()
        for slot in slots:
            self.db.refresh(slot)
        return slots

    def delete_slot(self, slot_id: str) -> None:
        """
        Remove a slot from availability, but only if empty
        """
        slot = self.get_slot_from_id(slot_id)
        if not slot:
            raise ValueError(f"Slot {slot_id} does not exist")
        if slot.event_id is not None:
            raise ValueError(f"Slot {slot_id} is not empty")
        self.db.delete(slot)
        self.db.commit()