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

from .schemas import UserRegistration, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    """
    Get all users in the system.
    
    Returns a list of all registered users with basic information.
    """
    try:
        users = db.query(Users).all()
        return [
            UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                created_at=user.created_at.isoformat() if user.created_at else datetime.utcnow().isoformat()
            )
            for user in users
        ]
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

        return UserResponse(
            id=new_user.id,
            email=new_user.email,
            name=new_user.name,
            created_at=new_user.created_at.isoformat() if new_user.created_at else datetime.utcnow().isoformat()
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
