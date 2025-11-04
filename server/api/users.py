"""
User-related API endpoints.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models import Users
from utils.auth import create_password_hash

from .schemas import UserRegistration, UserResponse, UserRole, UserPromoteResponse, RoleListResponse
from .auth import require_auth, require_admin
from utils.roles import get_user_with_roles, add_admin_role, get_users_by_role, UserRole as UtilsUserRole, add_attendee_role

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserResponse])
def get_all_users(user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    """
    Get all users in the system (admin only).
    
    Returns a list of all registered users with role information.
    """
    try:
        users = db.query(Users).all()
        user_responses = []
        for db_user in users:
            user_info = get_user_with_roles(db, db_user.id)
            if user_info:
                user_responses.append(UserResponse(
                    id=user_info['id'],
                    email=user_info['email'],
                    name=user_info['name'],
                    roles=user_info['roles'],
                    is_admin=user_info['is_admin'],
                    is_host=user_info['is_host'],
                    is_attendee=user_info['is_attendee'],
                    created_at=user_info['created_at'].isoformat() if user_info['created_at'] else datetime.utcnow().isoformat(),
                    updated_at=user_info['updated_at'].isoformat() if user_info.get('updated_at') else None
                ))
        return user_responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/register", response_model=UserResponse)
def add_user(user_data: UserRegistration, db: Session = Depends(get_db)):
    """
    Create a new user account.
    
    Validates email uniqueness, password confirmation, creates user with UUID,
    and stores securely hashed password in database.
    """
    try:
        # Check if email already exists
        existing_user = db.query(Users).filter(Users.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="Email already registered"
            )

        # Generate UUID for new user
        user_id = str(uuid.uuid4())

        # Hash password with salt
        password_hash, salt = create_password_hash(user_data.password)

        # Create new user
        new_user = Users(
            id=user_id,
            email=user_data.email,
            name=user_data.name,
            password_hash=password_hash,
            salt=salt
        )

        # Save to database
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Add default attendee role
        try:
            add_attendee_role(db, new_user.id)
        except Exception as e:
            # If attendee role creation fails, still return the user but log the error
            print(f"Failed to add attendee role to new user {new_user.id}: {e}")

        # Get user with role information
        user_with_roles = get_user_with_roles(db, new_user.id)
        if user_with_roles:
            return UserResponse(
                id=user_with_roles['id'],
                email=user_with_roles['email'],
                name=user_with_roles['name'],
                roles=user_with_roles['roles'],
                is_admin=user_with_roles['is_admin'],
                is_host=user_with_roles['is_host'],
                is_attendee=user_with_roles['is_attendee'],
                created_at=user_with_roles['created_at'].isoformat() if user_with_roles['created_at'] else datetime.utcnow().isoformat(),
                updated_at=user_with_roles['updated_at'].isoformat() if user_with_roles.get('updated_at') else None
            )
        else:
            # Fallback if role lookup fails
            return UserResponse(
                id=new_user.id,
                email=new_user.email,
                name=new_user.name,
                roles=[],
                is_admin=False,
                is_host=False,
                is_attendee=False,
                created_at=new_user.created_at.isoformat() if new_user.created_at else datetime.utcnow().isoformat(),
                updated_at=None
            )

    except IntegrityError as e:
        db.rollback()
        if "email" in str(e.orig):
            return UserResponse(
                id="",
                email="",
                name="",
                created_at="",
                error="Email already registered"
            )
        else:
            return UserResponse(
                id="",
                email="",
                name="",
                created_at="",
                error="Database constraint error"
            )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/me", response_model=UserResponse)
def get_current_user_info(user: dict = Depends(require_auth)):
    """
    Get current authenticated user's information including roles.
    
    Returns:
        User information with role details
    """
    try:
        created_at = user.get('created_at')
        updated_at = user.get('updated_at')
        
        return UserResponse(
            id=user['id'],
            email=user['email'],
            name=user['name'],
            roles=user['roles'],
            is_admin=user['is_admin'],
            is_host=user['is_host'],
            is_attendee=user['is_attendee'],
            created_at=created_at.isoformat() if created_at else datetime.utcnow().isoformat(),
            updated_at=updated_at.isoformat() if updated_at else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.patch("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: str,
    role_update: dict,
    user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update user role (admin only).
    
    Args:
        user_id: User ID to update
        role_update: Role update information (e.g., {"role": "host"})
        user: Current admin user
        db: Database session
        
    Returns:
        Updated user information
    """
    try:
        # Check if target user exists
        target_user = db.query(Users).filter(Users.id == user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get the new role from the request
        new_role = role_update.get("role")
        if not new_role:
            raise HTTPException(status_code=422, detail="Role is required")
        
        # Validate the role
        valid_roles = ["attendee", "host", "admin"]
        if new_role not in valid_roles:
            raise HTTPException(status_code=422, detail=f"Invalid role. Must be one of: {valid_roles}")
        
        # Add the new role (this will handle adding the appropriate role record)
        from utils.roles import add_attendee_role, add_host_role, add_admin_role
        
        if new_role == "attendee":
            add_attendee_role(db, user_id)
        elif new_role == "host":
            # First ensure user is an attendee
            attendee = add_attendee_role(db, user_id)  # This won't duplicate if already exists
            add_host_role(db, user_id, attendee.id)
        elif new_role == "admin":
            add_admin_role(db, user_id)
        
        # Get updated user info
        updated_user = get_user_with_roles(db, user_id)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse(
            id=updated_user['id'],
            email=updated_user['email'],
            name=updated_user['name'],
            roles=updated_user['roles'],
            is_admin=updated_user['is_admin'],
            is_host=updated_user['is_host'],
            is_attendee=updated_user['is_attendee'],
            created_at=updated_user['created_at'].isoformat() if updated_user['created_at'] else datetime.utcnow().isoformat(),
            updated_at=updated_user['updated_at'].isoformat() if updated_user.get('updated_at') else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{user_id}/promote-admin", response_model=UserPromoteResponse)
def promote_user_to_admin(
    user_id: str,
    user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Promote user to admin role (admin only).
    
    Args:
        user_id: User ID to promote
        user: Current admin user
        db: Database session
        
    Returns:
        Promotion response with updated user info
    """
    try:
        # Check if target user exists
        target_user = db.query(Users).filter(Users.id == user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Add admin role
        try:
            add_admin_role(db, user_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Get updated user info
        updated_user = get_user_with_roles(db, user_id)
        
        user_response = UserResponse(
            id=updated_user['id'],
            email=updated_user['email'],
            name=updated_user['name'],
            roles=updated_user['roles'],
            is_admin=updated_user['is_admin'],
            is_host=updated_user['is_host'],
            is_attendee=updated_user['is_attendee'],
            created_at=updated_user['created_at'].isoformat() if updated_user['created_at'] else datetime.utcnow().isoformat(),
            updated_at=updated_user['updated_at'].isoformat() if updated_user.get('updated_at') else None
        )
        
        return UserPromoteResponse(
            success=True,
            message="User promoted to admin successfully",
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/by-role/{role}", response_model=RoleListResponse)
def get_users_by_role_endpoint(
    role: UserRole,
    user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get all users with a specific role (admin only).
    
    Args:
        role: Role to filter by
        user: Current admin user
        db: Database session
        
    Returns:
        List of users with the specified role
    """
    try:
        # Convert API role enum to utils role enum
        utils_role = UtilsUserRole(role.value)
        
        # Get users with the specified role
        users = get_users_by_role(db, utils_role)
        
        # Convert to response format
        user_responses = []
        for db_user in users:
            user_info = get_user_with_roles(db, db_user.id)
            if user_info:
                user_responses.append(UserResponse(
                    id=user_info['id'],
                    email=user_info['email'],
                    name=user_info['name'],
                    roles=user_info['roles'],
                    is_admin=user_info['is_admin'],
                    is_host=user_info['is_host'],
                    is_attendee=user_info['is_attendee'],
                    created_at=user_info['created_at'].isoformat() if user_info['created_at'] else datetime.utcnow().isoformat(),
                    updated_at=user_info['updated_at'].isoformat() if user_info.get('updated_at') else None
                ))
        
        return RoleListResponse(
            users=user_responses,
            total=len(user_responses),
            role=role.value
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
