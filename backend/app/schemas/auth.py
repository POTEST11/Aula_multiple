"""Authentication schemas for register, login, and token responses."""

from datetime import datetime

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """Schema for user registration."""

    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2, max_length=255)


class LoginRequest(BaseModel):
    """Schema for user login."""

    email: str
    password: str


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Schema for user data in responses."""

    id: int
    email: str
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}
