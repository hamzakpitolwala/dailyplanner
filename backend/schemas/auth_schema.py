from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user registration requests."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    timezone: str = Field(default="UTC", max_length=50)


class UserLogin(BaseModel):
    """Schema for user login requests."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema returned when exposing user data."""

    id: UUID
    email: str
    timezone: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Schema for authentication token responses."""

    access_token: str
    token_type: str = "bearer"

class ChangePasswordRequest(BaseModel):
    """Changepasswordrequest."""
    old_password: str
    new_password: str = Field(min_length=8, max_length=128)
