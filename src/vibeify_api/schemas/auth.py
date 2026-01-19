"""Authentication schemas."""
import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from vibeify_api.models.user import User


class Token(BaseModel):
    """JWT token response schema."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data."""

    user_id: Optional[int] = None


class UserLogin(BaseModel):
    """User login request schema."""

    email: EmailStr
    password: str = Field(..., min_length=8)


class UserRegister(BaseModel):
    """User registration request schema."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(default=None, max_length=200)


class UserResponse(BaseModel):
    """User response schema (excludes sensitive fields)."""

    id: int
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class UserInDB(User):
    """User model for internal use (includes all fields)."""

    hashed_password: Optional[str] = None
