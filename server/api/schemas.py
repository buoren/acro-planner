"""
Pydantic models for API requests and responses.
"""


from pydantic import BaseModel, EmailStr, ValidationInfo, field_validator


class UserRegistration(BaseModel):
    """Schema for user registration request."""
    email: EmailStr
    name: str
    password: str
    password_confirm: str

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
    """Schema for user response."""
    id: str
    email: str
    name: str
    created_at: str
