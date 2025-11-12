"""
Tests for AttendeeManager functionality.
"""

import pytest
import ulid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from api.attendees import AttendeeManager
from models import Attendees, Users, Selections, Events, Conventions


class TestAttendeeManager:
    """Tests for AttendeeManager class."""

    def test_get_attendee_from_user_id_success(self, db_session):
        """Test getting attendee by user ID."""
        # Create user
        user = Users(
            id=str(ulid.new()),
            email="test@example.com",
            name="Test User",
            password_hash="hash",
            salt="salt"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create attendee
        attendee = Attendees(
            id=str(ulid.new()),
            user_id=user.id,
            convention_id=None,
            is_registered=False
        )
        db_session.add(attendee)
        db_session.commit()
        
        manager = AttendeeManager(db_session)
        result = manager.get_attendee_from_user_id(user.id)
        
        assert result is not None
        assert result.id == attendee.id
        assert result.user_id == user.id

    def test_get_attendee_from_user_id_not_found(self, db_session):
        """Test getting attendee for user without attendee record."""
        # Create user
        user = Users(
            id=str(ulid.new()),
            email="test@example.com",
            name="Test User",
            password_hash="hash",
            salt="salt"
        )
        db_session.add(user)
        db_session.commit()
        
        manager = AttendeeManager(db_session)
        result = manager.get_attendee_from_user_id(user.id)
        
        assert result is None

    def test_get_attendee_from_user_id_multiple_raises_error(self, db_session):
        """Test getting attendee when multiple records exist raises error."""
        # Create user
        user = Users(
            id=str(ulid.new()),
            email="test@example.com",
            name="Test User",
            password_hash="hash",
            salt="salt"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create convention
        convention = Conventions(
            id=str(ulid.new()),
            name="Test Convention",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=3)
        )
        db_session.add(convention)
        db_session.commit()
        
        # Create multiple attendees for same user
        attendee1 = Attendees(
            id=str(ulid.new()),
            user_id=user.id,
            convention_id=None,
            is_registered=False
        )
        attendee2 = Attendees(
            id=str(ulid.new()),
            user_id=user.id,
            convention_id=convention.id,
            is_registered=False
        )
        db_session.add_all([attendee1, attendee2])
        db_session.commit()
        
        manager = AttendeeManager(db_session)
        
        with pytest.raises(ValueError, match="Expected exactly 1 attendee"):
            manager.get_attendee_from_user_id(user.id)

    def test_is_attendee_true(self, db_session):
        """Test checking if user is attendee returns True."""
        # Create user
        user = Users(
            id=str(ulid.new()),
            email="test@example.com",
            name="Test User",
            password_hash="hash",
            salt="salt"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create attendee
        attendee = Attendees(
            id=str(ulid.new()),
            user_id=user.id,
            convention_id=None,
            is_registered=False
        )
        db_session.add(attendee)
        db_session.commit()
        
        manager = AttendeeManager(db_session)
        assert manager.is_attendee(user.id) is True

    def test_is_attendee_false(self, db_session):
        """Test checking if user is attendee returns False."""
        # Create user
        user = Users(
            id=str(ulid.new()),
            email="test@example.com",
            name="Test User",
            password_hash="hash",
            salt="salt"
        )
        db_session.add(user)
        db_session.commit()
        
        manager = AttendeeManager(db_session)
        assert manager.is_attendee(user.id) is False

    def test_is_attendee_with_convention_id(self, db_session):
        """Test checking if user is attendee for specific convention."""
        # Create user
        user = Users(
            id=str(ulid.new()),
            email="test@example.com",
            name="Test User",
            password_hash="hash",
            salt="salt"
        )
        db_session.add(user)
        db_session.commit()
        
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
        
        # Create attendee for convention1 only
        attendee = Attendees(
            id=str(ulid.new()),
            user_id=user.id,
            convention_id=convention1.id,
            is_registered=False
        )
        db_session.add(attendee)
        db_session.commit()
        
        manager = AttendeeManager(db_session)
        assert manager.is_attendee(user.id, convention1.id) is True
        assert manager.is_attendee(user.id, convention2.id) is False

    def test_add_attendee_role_general(self, db_session):
        """Test adding general attendee role."""
        # Create user
        user = Users(
            id=str(ulid.new()),
            email="test@example.com",
            name="Test User",
            password_hash="hash",
            salt="salt"
        )
        db_session.add(user)
        db_session.commit()
        
        manager = AttendeeManager(db_session)
        attendee = manager.add_attendee_role(user.id)
        
        assert attendee is not None
        assert attendee.user_id == user.id
        assert attendee.convention_id is None
        assert attendee.is_registered is False

    def test_add_attendee_role_duplicate_general(self, db_session):
        """Test adding duplicate general attendee role returns existing."""
        # Create user
        user = Users(
            id=str(ulid.new()),
            email="test@example.com",
            name="Test User",
            password_hash="hash",
            salt="salt"
        )
        db_session.add(user)
        db_session.commit()
        
        manager = AttendeeManager(db_session)
        attendee1 = manager.add_attendee_role(user.id)
        attendee2 = manager.add_attendee_role(user.id)
        
        assert attendee1.id == attendee2.id  # Should return same record

    def test_add_attendee_role_with_convention(self, db_session):
        """Test adding attendee role for specific convention."""
        # Create user
        user = Users(
            id=str(ulid.new()),
            email="test@example.com",
            name="Test User",
            password_hash="hash",
            salt="salt"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create convention
        convention = Conventions(
            id=str(ulid.new()),
            name="Test Convention",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=3)
        )
        db_session.add(convention)
        db_session.commit()
        
        manager = AttendeeManager(db_session)
        attendee = manager.add_attendee_role(user.id, convention.id)
        
        assert attendee is not None
        assert attendee.user_id == user.id
        assert attendee.convention_id == convention.id
        assert attendee.is_registered is False

    def test_get_attendee_list_from_convention_id(self, db_session):
        """Test getting all attendees for a convention."""
        # Create users
        user1 = Users(
            id=str(ulid.new()),
            email="user1@example.com",
            name="User 1",
            password_hash="hash",
            salt="salt"
        )
        user2 = Users(
            id=str(ulid.new()),
            email="user2@example.com",
            name="User 2",
            password_hash="hash",
            salt="salt"
        )
        db_session.add_all([user1, user2])
        db_session.commit()
        
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
        
        # Create attendees
        attendee1 = Attendees(
            id=str(ulid.new()),
            user_id=user1.id,
            convention_id=convention1.id,
            is_registered=False
        )
        attendee2 = Attendees(
            id=str(ulid.new()),
            user_id=user2.id,
            convention_id=convention1.id,
            is_registered=False
        )
        attendee3 = Attendees(
            id=str(ulid.new()),
            user_id=user1.id,
            convention_id=convention2.id,
            is_registered=False
        )
        db_session.add_all([attendee1, attendee2, attendee3])
        db_session.commit()
        
        manager = AttendeeManager(db_session)
        results = manager.get_attendee_list_from_convention_id(convention1.id)
        
        assert len(results) == 2
        assert {r.id for r in results} == {attendee1.id, attendee2.id}

    def test_get_users_by_role(self, db_session):
        """Test getting all users with attendee role."""
        # Create users
        user1 = Users(
            id=str(ulid.new()),
            email="user1@example.com",
            name="User 1",
            password_hash="hash",
            salt="salt"
        )
        user2 = Users(
            id=str(ulid.new()),
            email="user2@example.com",
            name="User 2",
            password_hash="hash",
            salt="salt"
        )
        user3 = Users(
            id=str(ulid.new()),
            email="user3@example.com",
            name="User 3",
            password_hash="hash",
            salt="salt"
        )
        db_session.add_all([user1, user2, user3])
        db_session.commit()
        
        # Create attendees for user1 and user2 only
        attendee1 = Attendees(
            id=str(ulid.new()),
            user_id=user1.id,
            convention_id=None,
            is_registered=False
        )
        attendee2 = Attendees(
            id=str(ulid.new()),
            user_id=user2.id,
            convention_id=None,
            is_registered=False
        )
        db_session.add_all([attendee1, attendee2])
        db_session.commit()
        
        manager = AttendeeManager(db_session)
        results = manager.get_users_by_role()
        
        assert len(results) == 2
        assert {r.id for r in results} == {user1.id, user2.id}

    def test_remove_attendee_role_general(self, db_session):
        """Test removing general attendee role."""
        # Create user
        user = Users(
            id=str(ulid.new()),
            email="test@example.com",
            name="Test User",
            password_hash="hash",
            salt="salt"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create attendee
        attendee = Attendees(
            id=str(ulid.new()),
            user_id=user.id,
            convention_id=None,
            is_registered=False
        )
        db_session.add(attendee)
        db_session.commit()
        
        manager = AttendeeManager(db_session)
        result = manager.remove_attendee_role(user.id)
        
        assert result is True
        deleted = db_session.query(Attendees).filter(Attendees.id == attendee.id).first()
        assert deleted is None

    def test_remove_attendee_role_not_found(self, db_session):
        """Test removing attendee role when it doesn't exist."""
        # Create user
        user = Users(
            id=str(ulid.new()),
            email="test@example.com",
            name="Test User",
            password_hash="hash",
            salt="salt"
        )
        db_session.add(user)
        db_session.commit()
        
        manager = AttendeeManager(db_session)
        result = manager.remove_attendee_role(user.id)
        
        assert result is False

    def test_remove_attendee_role_with_convention(self, db_session):
        """Test removing attendee role for specific convention."""
        # Create user
        user = Users(
            id=str(ulid.new()),
            email="test@example.com",
            name="Test User",
            password_hash="hash",
            salt="salt"
        )
        db_session.add(user)
        db_session.commit()
        
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
        
        # Create attendees for both conventions
        attendee1 = Attendees(
            id=str(ulid.new()),
            user_id=user.id,
            convention_id=convention1.id,
            is_registered=False
        )
        attendee2 = Attendees(
            id=str(ulid.new()),
            user_id=user.id,
            convention_id=convention2.id,
            is_registered=False
        )
        db_session.add_all([attendee1, attendee2])
        db_session.commit()
        
        manager = AttendeeManager(db_session)
        result = manager.remove_attendee_role(user.id, convention1.id)
        
        assert result is True
        # Convention1 attendee should be deleted
        deleted1 = db_session.query(Attendees).filter(Attendees.id == attendee1.id).first()
        assert deleted1 is None
        # Convention2 attendee should still exist
        existing2 = db_session.query(Attendees).filter(Attendees.id == attendee2.id).first()
        assert existing2 is not None

    def test_sign_up_for_convention_success(self, db_session):
        """Test signing up for a convention."""
        # Create user
        user = Users(
            id=str(ulid.new()),
            email="test@example.com",
            name="Test User",
            password_hash="hash",
            salt="salt"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create convention
        convention = Conventions(
            id=str(ulid.new()),
            name="Test Convention",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=3)
        )
        db_session.add(convention)
        db_session.commit()
        
        # Create attendee
        attendee = Attendees(
            id=str(ulid.new()),
            user_id=user.id,
            convention_id=None,
            is_registered=False
        )
        db_session.add(attendee)
        db_session.commit()
        
        manager = AttendeeManager(db_session)
        result = manager.sign_up_for_convention(user.id, convention.id)
        
        assert result is not None
        assert result.convention_id == convention.id
        assert result.is_registered is False  # Not yet registered (not paid)

    def test_sign_up_for_convention_not_attendee(self, db_session):
        """Test signing up when user is not an attendee raises error."""
        # Create user
        user = Users(
            id=str(ulid.new()),
            email="test@example.com",
            name="Test User",
            password_hash="hash",
            salt="salt"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create convention
        convention = Conventions(
            id=str(ulid.new()),
            name="Test Convention",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=3)
        )
        db_session.add(convention)
        db_session.commit()
        
        manager = AttendeeManager(db_session)
        
        with pytest.raises(ValueError, match="User.*is not an attendee"):
            manager.sign_up_for_convention(user.id, convention.id)

    def test_register_for_convention_success(self, db_session):
        """Test registering for a convention (after payment)."""
        # Create user
        user = Users(
            id=str(ulid.new()),
            email="test@example.com",
            name="Test User",
            password_hash="hash",
            salt="salt"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create convention
        convention = Conventions(
            id=str(ulid.new()),
            name="Test Convention",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=3)
        )
        db_session.add(convention)
        db_session.commit()
        
        # Create attendee
        attendee = Attendees(
            id=str(ulid.new()),
            user_id=user.id,
            convention_id=convention.id,
            is_registered=False
        )
        db_session.add(attendee)
        db_session.commit()
        
        manager = AttendeeManager(db_session)
        result = manager.register_for_convention(user.id, convention.id)
        
        assert result is not None
        assert result.is_registered is True  # Now registered (paid)

    def test_register_for_convention_not_attendee(self, db_session):
        """Test registering when user is not an attendee raises error."""
        # Create user
        user = Users(
            id=str(ulid.new()),
            email="test@example.com",
            name="Test User",
            password_hash="hash",
            salt="salt"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create convention
        convention = Conventions(
            id=str(ulid.new()),
            name="Test Convention",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=3)
        )
        db_session.add(convention)
        db_session.commit()
        
        manager = AttendeeManager(db_session)
        
        with pytest.raises(ValueError, match="User.*is not an attendee"):
            manager.register_for_convention(user.id, convention.id)

    def test_show_interest_success(self, db_session):
        """Test showing interest in an event."""
        # Create user
        user = Users(
            id=str(ulid.new()),
            email="test@example.com",
            name="Test User",
            password_hash="hash",
            salt="salt"
        )
        db_session.add(user)
        db_session.commit()
        
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
        
        # Create attendee
        attendee = Attendees(
            id=str(ulid.new()),
            user_id=user.id,
            convention_id=convention.id,
            is_registered=False
        )
        db_session.add(attendee)
        db_session.commit()
        
        manager = AttendeeManager(db_session)
        selection = manager.show_interest(user.id, event.id)
        
        assert selection is not None
        assert selection.attendee_id == attendee.id
        assert selection.event_id == event.id
        assert selection.is_selected is False  # Just interest, not registered

    def test_show_interest_not_attendee(self, db_session):
        """Test showing interest when user is not an attendee raises error."""
        # Create user
        user = Users(
            id=str(ulid.new()),
            email="test@example.com",
            name="Test User",
            password_hash="hash",
            salt="salt"
        )
        db_session.add(user)
        db_session.commit()
        
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
        
        manager = AttendeeManager(db_session)
        
        with pytest.raises(ValueError, match="User.*is not an attendee"):
            manager.show_interest(user.id, event.id)

    def test_show_interest_event_not_exists(self, db_session):
        """Test showing interest in non-existent event raises error."""
        # Create user
        user = Users(
            id=str(ulid.new()),
            email="test@example.com",
            name="Test User",
            password_hash="hash",
            salt="salt"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create attendee
        attendee = Attendees(
            id=str(ulid.new()),
            user_id=user.id,
            convention_id=None,
            is_registered=False
        )
        db_session.add(attendee)
        db_session.commit()
        
        manager = AttendeeManager(db_session)
        
        with pytest.raises(ValueError, match="Event.*does not exist"):
            manager.show_interest(user.id, "nonexistent-event-id")

    def test_show_interest_duplicate(self, db_session):
        """Test showing interest twice raises error."""
        # Create user
        user = Users(
            id=str(ulid.new()),
            email="test@example.com",
            name="Test User",
            password_hash="hash",
            salt="salt"
        )
        db_session.add(user)
        db_session.commit()
        
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
        
        # Create attendee
        attendee = Attendees(
            id=str(ulid.new()),
            user_id=user.id,
            convention_id=convention.id,
            is_registered=False
        )
        db_session.add(attendee)
        db_session.commit()
        
        manager = AttendeeManager(db_session)
        manager.show_interest(user.id, event.id)
        
        with pytest.raises(ValueError, match="already has interest"):
            manager.show_interest(user.id, event.id)

    def test_register_for_event_success(self, db_session):
        """Test registering for an event."""
        # Create user
        user = Users(
            id=str(ulid.new()),
            email="test@example.com",
            name="Test User",
            password_hash="hash",
            salt="salt"
        )
        db_session.add(user)
        db_session.commit()
        
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
        
        # Create attendee
        attendee = Attendees(
            id=str(ulid.new()),
            user_id=user.id,
            convention_id=convention.id,
            is_registered=False
        )
        db_session.add(attendee)
        db_session.commit()
        
        manager = AttendeeManager(db_session)
        selection = manager.register_for_event(user.id, event.id)
        
        assert selection is not None
        assert selection.attendee_id == attendee.id
        assert selection.event_id == event.id
        assert selection.is_selected is True  # Registered, not just interested

