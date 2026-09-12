"""Authentication schemas."""

from pydantic import BaseModel, EmailStr
from uuid import UUID


class TokenData(BaseModel):
    """JWT token payload data."""

    user_id: str
    role: str
    clinic_id: str


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str


class UserCreate(BaseModel):
    """User registration data."""

    email: EmailStr
    password: str
    full_name: str
    role: str  # admin, doctor, nurse, user
    clinic_id: UUID


class UserResponse(BaseModel):
    """User info response."""

    id: str
    email: str
    full_name: str
    role: str
    clinic_id: UUID

    class Config:
        from_attributes = True
