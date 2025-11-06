"""
Pydantic models for API requests and responses.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, EmailStr, ValidationInfo, field_validator


class UserRole(str, Enum):
    """User role enumeration for API validation."""
    ATTENDEE = "attendee"
    HOST = "host"
    ADMIN = "admin"


class UserRegistration(BaseModel):
    """Schema for user registration request."""
    email: EmailStr
    name: str
    password: str
    password_confirm: str
    role: Optional[UserRole] = UserRole.ATTENDEE  # Default role is attendee

    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

    @field_validator('password_confirm')
    @classmethod
    def passwords_match(cls, v: str, info: ValidationInfo) -> str:
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v


class UserResponse(BaseModel):
    """Schema for user response with role information."""
    id: str
    email: str
    name: str
    roles: List[str]
    is_admin: bool
    is_host: bool
    is_attendee: bool
    created_at: str
    updated_at: Optional[str] = None


class UserRoleUpdate(BaseModel):
    """Schema for updating user roles."""
    role: UserRole
    action: str  # "add" or "remove"

    @field_validator('action')
    @classmethod
    def validate_action(cls, v: str) -> str:
        if v not in ["add", "remove"]:
            raise ValueError('Action must be "add" or "remove"')
        return v


class UserPromoteRequest(BaseModel):
    """Schema for promoting user to admin."""
    user_id: str


class UserPromoteResponse(BaseModel):
    """Schema for promotion response."""
    success: bool
    message: str
    user: Optional[UserResponse] = None


class RoleListResponse(BaseModel):
    """Schema for listing users by role."""
    users: List[UserResponse]
    total: int
    role: str
