"""
Role detection and management utilities.

This module provides functions to detect user roles based on foreign key relationships
in the attendees, hosts, and admins tables.
"""

from enum import Enum
from typing import List, Set
from sqlalchemy.orm import Session
from models import Users, Attendees, Hosts, Admins


class UserRole(Enum):
    """User role enumeration for validation and API responses."""
    ATTENDEE = "attendee"
    HOST = "host"
    ADMIN = "admin"


def get_user_roles(db: Session, user_id: str) -> Set[UserRole]:
    """
    Get all roles for a user by checking foreign key relationships.
    
    Args:
        db: Database session
        user_id: User ID to check roles for
        
    Returns:
        Set of UserRole enums that the user has
    """
    roles = set()
    
    # Check if user is an attendee
    attendee = db.query(Attendees).filter(Attendees.user_id == user_id).first()
    if attendee:
        roles.add(UserRole.ATTENDEE)
    
    # Check if user is a host
    host = db.query(Hosts).filter(Hosts.user_id == user_id).first()
    if host:
        roles.add(UserRole.HOST)
    
    # Check if user is an admin
    admin = db.query(Admins).filter(Admins.user_id == user_id).first()
    if admin:
        roles.add(UserRole.ADMIN)
    
    return roles


def get_user_roles_list(db: Session, user_id: str) -> List[str]:
    """
    Get user roles as a list of strings.
    
    Args:
        db: Database session
        user_id: User ID to check roles for
        
    Returns:
        List of role strings
    """
    roles = get_user_roles(db, user_id)
    return [role.value for role in roles]


def is_admin(db: Session, user_id: str) -> bool:
    """Check if user has admin role."""
    admin = db.query(Admins).filter(Admins.user_id == user_id).first()
    return admin is not None


def is_host(db: Session, user_id: str) -> bool:
    """Check if user has host role."""
    host = db.query(Hosts).filter(Hosts.user_id == user_id).first()
    return host is not None


def is_attendee(db: Session, user_id: str) -> bool:
    """Check if user has attendee role."""
    attendee = db.query(Attendees).filter(Attendees.user_id == user_id).first()
    return attendee is not None


def is_host_or_admin(db: Session, user_id: str) -> bool:
    """Check if user has host or admin role."""
    return is_host(db, user_id) or is_admin(db, user_id)


def add_admin_role(db: Session, user_id: str) -> Admins:
    """
    Add admin role to a user.
    
    Args:
        db: Database session
        user_id: User ID to promote
        
    Returns:
        Created Admins record
        
    Raises:
        ValueError: If user already has admin role
    """
    import ulid
    
    # Check if user already has admin role
    existing_admin = db.query(Admins).filter(Admins.user_id == user_id).first()
    if existing_admin:
        raise ValueError("User already has admin role")
    
    # Create admin record
    admin = Admins(
        id=str(ulid.new()),
        user_id=user_id
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    return admin


def add_host_role(db: Session, user_id: str, attendee_id: str = None) -> Hosts:
    """
    Add host role to a user.
    
    Args:
        db: Database session
        user_id: User ID to promote
        attendee_id: Attendee ID (if None, will look up or create)
        
    Returns:
        Created Hosts record
        
    Raises:
        ValueError: If user already has host role
    """
    import ulid
    
    # Check if user already has host role
    existing_host = db.query(Hosts).filter(Hosts.user_id == user_id).first()
    if existing_host:
        raise ValueError("User already has host role")
    
    # If no attendee_id provided, find or create attendee record
    if not attendee_id:
        attendee = db.query(Attendees).filter(Attendees.user_id == user_id).first()
        if not attendee:
            # User must be an attendee before becoming a host
            raise ValueError("User must be an attendee before becoming a host")
        attendee_id = attendee.id
    
    # Create host record
    host = Hosts(
        id=str(ulid.new()),
        user_id=user_id,
        attendee_id=attendee_id,
        photos=None,
        links=None
    )
    
    db.add(host)
    db.commit()
    db.refresh(host)
    
    return host


def add_attendee_role(db: Session, user_id: str, convention_id: str = None) -> Attendees:
    """
    Add attendee role to a user.
    
    Args:
        db: Database session
        user_id: User ID to add as attendee
        convention_id: Convention ID (optional, for convention-specific attendee record)
        
    Returns:
        Created Attendees record
        
    Note:
        If convention_id is None, creates a general attendee record.
        Users can have multiple attendee records for different conventions.
    """
    import ulid
    
    # For general attendee role (no specific convention), check if already exists
    if not convention_id:
        existing_attendee = db.query(Attendees).filter(
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
    
    db.add(attendee)
    db.commit()
    db.refresh(attendee)
    
    return attendee


def remove_admin_role(db: Session, user_id: str) -> bool:
    """
    Remove admin role from a user.
    
    Args:
        db: Database session
        user_id: User ID to demote
        
    Returns:
        True if role was removed, False if user didn't have admin role
    """
    admin = db.query(Admins).filter(Admins.user_id == user_id).first()
    if admin:
        db.delete(admin)
        db.commit()
        return True
    return False


def remove_host_role(db: Session, user_id: str) -> bool:
    """
    Remove host role from a user.
    
    Args:
        db: Database session
        user_id: User ID to demote
        
    Returns:
        True if role was removed, False if user didn't have host role
    """
    host = db.query(Hosts).filter(Hosts.user_id == user_id).first()
    if host:
        db.delete(host)
        db.commit()
        return True
    return False


def get_users_by_role(db: Session, role: UserRole) -> List[Users]:
    """
    Get all users with a specific role.
    
    Args:
        db: Database session
        role: Role to filter by
        
    Returns:
        List of Users with the specified role
    """
    if role == UserRole.ADMIN:
        # Join with admins table
        return db.query(Users).join(Admins, Users.id == Admins.user_id).all()
    elif role == UserRole.HOST:
        # Join with hosts table
        return db.query(Users).join(Hosts, Users.id == Hosts.user_id).all()
    elif role == UserRole.ATTENDEE:
        # Join with attendees table
        return db.query(Users).join(Attendees, Users.id == Attendees.user_id).all()
    else:
        return []


def get_user_with_roles(db: Session, user_id: str) -> dict:
    """
    Get user information with all their roles.
    
    Args:
        db: Database session
        user_id: User ID to get information for
        
    Returns:
        Dictionary with user info and roles
    """
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        return None
    
    roles = get_user_roles_list(db, user_id)
    
    # Get role-specific IDs if user has those roles
    host_id = None
    attendee_id = None
    admin_id = None
    
    if UserRole.HOST.value in roles:
        host = db.query(Hosts).filter(Hosts.user_id == user_id).first()
        if host:
            host_id = host.id
    
    if UserRole.ATTENDEE.value in roles:
        attendee = db.query(Attendees).filter(Attendees.user_id == user_id).first()
        if attendee:
            attendee_id = attendee.id
    
    if UserRole.ADMIN.value in roles:
        admin = db.query(Admins).filter(Admins.user_id == user_id).first()
        if admin:
            admin_id = admin.id
    
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "roles": roles,
        "is_admin": UserRole.ADMIN.value in roles,
        "is_host": UserRole.HOST.value in roles,
        "is_attendee": UserRole.ATTENDEE.value in roles,
        "host_id": host_id,
        "attendee_id": attendee_id,
        "admin_id": admin_id,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }