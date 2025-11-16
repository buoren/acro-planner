"""
Pydantic models for API requests and responses.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
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


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request."""
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    """Schema for forgot password response."""
    success: bool
    message: str


class ResetPasswordRequest(BaseModel):
    """Schema for reset password request."""
    token: str
    new_password: str
    confirm_password: str

    @field_validator('new_password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v: str, info: ValidationInfo) -> str:
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v


class ResetPasswordResponse(BaseModel):
    """Schema for reset password response."""
    success: bool
    message: str


# Convention Management Schemas
class LocationCreate(BaseModel):
    """Schema for creating a location."""
    name: str
    description: Optional[str] = None
    capacity: Optional[int] = None
    address: Optional[str] = None
    
    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Location name cannot be empty')
        return v.strip()


class LocationUpdate(BaseModel):
    """Schema for updating a location."""
    name: Optional[str] = None
    description: Optional[str] = None
    capacity: Optional[int] = None
    address: Optional[str] = None


class LocationResponse(BaseModel):
    """Schema for location response."""
    id: str
    name: str
    description: Optional[str] = None
    capacity: Optional[int] = None
    address: Optional[str] = None
    equipment: List[Dict[str, Any]] = []
    created_at: str
    updated_at: Optional[str] = None


class ConventionCreate(BaseModel):
    """Schema for creating a convention."""
    name: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    location_ids: List[str] = []
    
    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Convention name cannot be empty')
        return v.strip()
    
    @field_validator('end_date')
    @classmethod
    def end_after_start(cls, v: datetime, info: ValidationInfo) -> datetime:
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('End date must be after start date')
        return v


class ConventionUpdate(BaseModel):
    """Schema for updating a convention."""
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location_ids: Optional[List[str]] = None


class ConventionResponse(BaseModel):
    """Schema for convention response."""
    id: str
    name: str
    description: Optional[str] = None
    start_date: str
    end_date: str
    locations: List[LocationResponse] = []
    event_slots: List[Dict[str, Any]] = []
    created_at: str
    updated_at: Optional[str] = None


# Event Slot Schemas
class EventSlotCreate(BaseModel):
    """Schema for creating an event slot."""
    convention_id: str
    start_time: datetime
    end_time: datetime
    location_id: str
    
    @field_validator('end_time')
    @classmethod
    def end_after_start(cls, v: datetime, info: ValidationInfo) -> datetime:
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('End time must be after start time')
        return v


class EventSlotUpdate(BaseModel):
    """Schema for updating an event slot."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location_id: Optional[str] = None


class EventSlotResponse(BaseModel):
    """Schema for event slot response."""
    id: str
    convention_id: str
    start_time: str
    end_time: str
    location: LocationResponse
    created_at: str
    updated_at: Optional[str] = None


# Prerequisite Schemas
class PrerequisiteCreate(BaseModel):
    """Schema for creating a prerequisite."""
    name: str
    description: str
    parent_prerequisite_ids: List[str] = []
    
    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Prerequisite name cannot be empty')
        return v.strip()


class PrerequisiteUpdate(BaseModel):
    """Schema for updating a prerequisite."""
    name: Optional[str] = None
    description: Optional[str] = None
    parent_prerequisite_ids: Optional[List[str]] = None


class PrerequisiteResponse(BaseModel):
    """Schema for prerequisite response."""
    id: str
    name: str
    description: str
    parent_prerequisites: List[Dict[str, str]] = []
    all_prerequisites: List[Dict[str, str]] = []
    created_at: str
    updated_at: Optional[str] = None


# Equipment Schemas
class EquipmentCreate(BaseModel):
    """Schema for creating equipment."""
    name: str
    description: Optional[str] = None
    location_id: str
    quantity: int = 1
    
    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Equipment name cannot be empty')
        return v.strip()
    
    @field_validator('quantity')
    @classmethod
    def quantity_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError('Quantity must be at least 1')
        return v


class EquipmentUpdate(BaseModel):
    """Schema for updating equipment."""
    name: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[int] = None
    location_id: Optional[str] = None


class EquipmentResponse(BaseModel):
    """Schema for equipment response."""
    id: str
    name: str
    description: Optional[str] = None
    location_id: str
    location_name: str
    quantity: int
    created_at: str
    updated_at: Optional[str] = None


# Workshop (Event) Schemas
class WorkshopCreate(BaseModel):
    """Schema for creating a workshop."""
    name: str
    description: str
    host_id: str
    max_students: int
    prerequisite_ids: List[str] = []
    equipment_ids: List[str] = []
    
    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Workshop name cannot be empty')
        return v.strip()
    
    @field_validator('max_students')
    @classmethod
    def max_students_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError('Max students must be at least 1')
        return v


class WorkshopUpdate(BaseModel):
    """Schema for updating a workshop."""
    name: Optional[str] = None
    description: Optional[str] = None
    max_students: Optional[int] = None
    prerequisite_ids: Optional[List[str]] = None
    equipment_ids: Optional[List[str]] = None


class WorkshopResponse(BaseModel):
    """Schema for workshop response."""
    id: str
    name: str
    description: str
    host_id: str
    host_name: str
    max_students: int
    current_students: int
    prerequisites: List[PrerequisiteResponse] = []
    equipment: List[EquipmentResponse] = []
    event_slots: List[EventSlotResponse] = []
    created_at: str
    updated_at: Optional[str] = None


# Host Availability Schemas
class HostAvailabilityCreate(BaseModel):
    """Schema for setting host availability."""
    host_id: str
    event_slot_ids: List[str]


class HostAvailabilityResponse(BaseModel):
    """Schema for host availability response."""
    host_id: str
    host_name: str
    available_slots: List[EventSlotResponse]
    workshops: List[WorkshopResponse]


# Attendee Selection Schemas
class WorkshopSelectionCreate(BaseModel):
    """Schema for selecting a workshop."""
    attendee_id: str
    workshop_id: str
    event_slot_id: str
    commitment_level: str = "interested"  # interested, maybe, committed
    
    @field_validator('commitment_level')
    @classmethod
    def validate_commitment(cls, v: str) -> str:
        if v not in ["interested", "maybe", "committed"]:
            raise ValueError('Commitment level must be "interested", "maybe", or "committed"')
        return v


class WorkshopSelectionUpdate(BaseModel):
    """Schema for updating workshop selection."""
    commitment_level: str
    
    @field_validator('commitment_level')
    @classmethod
    def validate_commitment(cls, v: str) -> str:
        if v not in ["interested", "maybe", "committed"]:
            raise ValueError('Commitment level must be "interested", "maybe", or "committed"')
        return v


class WorkshopSelectionResponse(BaseModel):
    """Schema for workshop selection response."""
    id: str
    attendee_id: str
    attendee_name: str
    workshop: WorkshopResponse
    event_slot: EventSlotResponse
    commitment_level: str
    created_at: str
    updated_at: Optional[str] = None


# Attendee Schedule Schema
class AttendeeScheduleResponse(BaseModel):
    """Schema for attendee schedule response."""
    attendee_id: str
    attendee_name: str
    selections: List[WorkshopSelectionResponse]
    committed_count: int
    interested_count: int
    maybe_count: int


# Workshop Browse/Filter Schemas
class WorkshopFilterParams(BaseModel):
    """Schema for filtering workshops."""
    convention_id: Optional[str] = None
    can_fulfill_prerequisites: Optional[bool] = None
    attendee_capabilities: Optional[List[str]] = None
    event_slot_id: Optional[str] = None
    has_space: Optional[bool] = True


class WorkshopShareResponse(BaseModel):
    """Schema for sharing a workshop link."""
    workshop_id: str
    workshop_name: str
    share_url: str
    description: str


# Convention Registration Schemas
class ConventionRegistrationResponse(BaseModel):
    """Schema for convention registration response."""
    registration_id: str
    convention_id: str
    convention_name: str
    attendee_id: str
    attendee_name: str
    is_registered: bool
    created_at: str


class AttendeeConventionsResponse(BaseModel):
    """Schema for attendee's registered conventions."""
    attendee_id: str
    attendee_name: str
    conventions: List[ConventionResponse]


# Event-to-Slot Assignment Schemas
class WorkshopSlotAssignmentCreate(BaseModel):
    """Schema for assigning workshop to slot."""
    workshop_id: str
    event_slot_id: str


class WorkshopSlotAssignmentResponse(BaseModel):
    """Schema for workshop slot assignment response."""
    workshop: WorkshopResponse
    event_slot: EventSlotResponse
    assigned_at: str


class SlotWorkshopResponse(BaseModel):
    """Schema for getting workshop assigned to a slot."""
    event_slot: EventSlotResponse
    workshop: Optional[WorkshopResponse] = None


# Bulk Slot Creation Schemas
class TimeSlotCreate(BaseModel):
    """Schema for time slot definition."""
    start_time: str  # Format: "09:00"
    end_time: str    # Format: "10:30"
    
    @field_validator('start_time', 'end_time')
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        import re
        if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', v):
            raise ValueError('Time must be in HH:MM format')
        return v


class BulkSlotCreationRequest(BaseModel):
    """Schema for bulk slot creation."""
    convention_id: str
    location_ids: List[str]
    time_slots: List[TimeSlotCreate]
    number_of_days: int
    
    @field_validator('number_of_days')
    @classmethod
    def validate_days(cls, v: int) -> int:
        if v < 1 or v > 30:
            raise ValueError('Number of days must be between 1 and 30')
        return v
    
    @field_validator('time_slots')
    @classmethod
    def validate_time_slots(cls, v: List[TimeSlotCreate]) -> List[TimeSlotCreate]:
        if len(v) == 0:
            raise ValueError('At least one time slot is required')
        if len(v) > 20:
            raise ValueError('Maximum 20 time slots allowed')
        return v


class BulkSlotCreationResponse(BaseModel):
    """Schema for bulk slot creation response."""
    convention_id: str
    total_slots_created: int
    slots: List[EventSlotResponse]
