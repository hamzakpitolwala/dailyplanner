from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user registration requests."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    username: str = Field(min_length=3, max_length=64)


class UserLogin(BaseModel):
    """Schema for user login requests."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema returned when exposing user data."""

    id: int
    email: str
    username: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Schema for authentication token responses."""

    access_token: str
    token_type: str = "bearer"