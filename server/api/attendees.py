"""
File for attendee-related functionality.
"""

import ulid
from sqlalchemy.orm import Session  
from typing import Optional, List
from models import Attendees, Users, Selections, Events

class AttendeeManager:
    def __init__(self, db: Session):
        self.db = db

    def get_attendee_from_user_id(self, user_id: str) -> Optional[Attendees]:
        """
        Get attendee record for a user.
        
        Args:
            user_id: User ID to get attendee for
            
        Returns:
            Attendees record if found, None otherwise
        """
        attendees = self.db.query(Attendees).filter(Attendees.user_id == user_id).all()
        if not attendees:
            return None
        if len(attendees) != 1:
            raise ValueError(f"Expected exactly 1 attendee for user {user_id}, but got {len(attendees)}")
        return attendees[0]

    def is_attendee(self, user_id: str, convention_id: str = None) -> bool:
        """
        Check if user has attendee role.
        
        Args:
            user_id: User ID to check
            convention_id: Optional convention ID to check for specific convention
            
        Returns:
            True if user is an attendee, False otherwise
        """
        query = self.db.query(Attendees).filter(Attendees.user_id == user_id)
        if convention_id is not None:
            query = query.filter(Attendees.convention_id == convention_id)
        attendee = query.first()
        return attendee is not None

    def add_attendee_role(self, user_id: str, convention_id: str = None) -> Attendees:
        """
        Add attendee role to a user.
        
        Args:
            user_id: User ID to add as attendee
            convention_id: Convention ID (optional, for convention-specific attendee record)
            
        Returns:
            Created Attendees record
            
        Note:
            If convention_id is None, creates a general attendee record.
            Users can have multiple attendee records for different conventions.
            If a general attendee record already exists, returns the existing one.
        """
        # For general attendee role (no specific convention), check if already exists
        if not convention_id:
            existing_attendee = self.db.query(Attendees).filter(
                Attendees.user_id == user_id,
                Attendees.convention_id.is_(None)
            ).first()
            if existing_attendee:
                return existing_attendee
        
        # Create attendee record
        attendee = Attendees(
            id=str(ulid.new()),
            user_id=user_id,
            convention_id=convention_id,
            is_registered=False
        )
        
        self.db.add(attendee)
        self.db.commit()
        self.db.refresh(attendee)
        
        return attendee

    def get_attendee_list_from_convention_id(self, convention_id: str) -> List[Attendees]:
        """
        Get all attendees for a convention.
        
        Args:
            convention_id: Convention ID to get attendees for
            
        Returns:
            List of Attendees records if found, empty list otherwise
        """
        return self.db.query(Attendees).filter(Attendees.convention_id == convention_id).all()

    def get_users_by_role(self) -> List[Users]:
        """
        Get all users with attendee role.
        
        Returns:
            List of Users who have attendee role
        """
        return self.db.query(Users).join(Attendees, Users.id == Attendees.user_id).all()

    def remove_attendee_role(self, user_id: str, convention_id: str = None) -> bool:
        """
        Remove attendee role from a user.
        
        Args:
            user_id: User ID to remove attendee role from
            convention_id: Optional convention ID to remove specific convention attendee record
            
        Returns:
            True if attendee role was removed, False if it didn't exist
        """
        query = self.db.query(Attendees).filter(Attendees.user_id == user_id)
        if convention_id is not None:
            query = query.filter(Attendees.convention_id == convention_id)
        else:
            query = query.filter(Attendees.convention_id.is_(None))
        
        attendee = query.first()
        if attendee:
            self.db.delete(attendee)
            self.db.commit()
            return True
        return False


    def sign_up_for_convention(self, user_id: str, convention_id: str) -> Attendees:
        """
        Register a user for a convention.
        
        Args:
            user_id: User ID to register
            convention_id: Convention ID to register for
            
        Returns:
            Attendees record if registration was successful, None otherwise
        """
        attendee = self.get_attendee_from_user_id(user_id)
        if not attendee:
            raise ValueError(f"User {user_id} is not an attendee")
        attendee.is_registered = False
        attendee.convention_id = convention_id
        self.db.commit()
        self.db.refresh(attendee)
        return attendee

    def register_for_convention(self, user_id: str, convention_id: str) -> Attendees:
        """
        Register a user for a convention.
        
        Args:
            user_id: User ID to register
            convention_id: Convention ID to register for
            
        Returns:
            Attendees record if registration was successful, None otherwise
        """
        attendee = self.get_attendee_from_user_id(user_id)
        if not attendee:
            raise ValueError(f"User {user_id} is not an attendee")
        attendee.is_registered = True
        self.db.commit()
        self.db.refresh(attendee)
        return attendee
        
    def show_interest(self, user_id: str, event_id: str) -> Selections:
        """
        Show interest in an event by adding it to your selections.  This doesn't mean
        you're necessarily going to go, but rather a soft "yes"
        
        Args:
            user_id: User ID to show interest
            event_id: Event ID to show interest for
            
        Returns:
            Selections record if interest was shown, None otherwise
        """
        attendee = self.get_attendee_from_user_id(user_id)
        if not attendee:
            raise ValueError(f"User {user_id} is not an attendee")
        if not self.db.query(Events).filter(Events.id == event_id).first():
            raise ValueError(f"Event {event_id} does not exist")
        if self.db.query(Selections).filter(Selections.attendee_id == attendee.id, Selections.event_id == event_id).first():
            raise ValueError(f"User {user_id} already has interest in event {event_id}")
        selection = Selections(
            id=str(ulid.new()),
            attendee_id=self.get_attendee_from_user_id(user_id).id,
            event_id=event_id,
            is_selected=False
        )
        self.db.add(selection)
        self.db.commit()
        self.db.refresh(selection)
        return selection

    def register_for_event(self, user_id: str, event_id: str) -> Selections:
        """
        Register for an event by adding it to your selections and marking it as selected.
        
        Args:
            user_id: User ID to register
            event_id: Event ID to register for
            
        Returns:
            Selections record if registration was successful, None otherwise
        """
        selection = self.show_interest(user_id, event_id)
        # In the future we may want to check to see if there's enough room
        # for the event, but for now we'll just mark it as selected.
        selection.is_selected = True
        self.db.commit()
        self.db.refresh(selection)
        return selection