"""User model."""
from typing import Optional

from sqlmodel import Field, Relationship

from vibeify_api.models.base import BaseModel


class User(BaseModel, table=True):
    """User model representing users in the system."""

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    username: str = Field(unique=True, index=True, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=200)
    is_active: bool = Field(default=True)
    hashed_password: Optional[str] = Field(default=None)
