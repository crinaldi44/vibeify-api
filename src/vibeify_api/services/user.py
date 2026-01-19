"""User service for business logic."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from vibeify_api.models.user import User
from vibeify_api.services.base import BaseService


class UserService(BaseService[User]):
    """Service for user-related business logic."""

    def __init__(self, session: AsyncSession):
        """Initialize user service."""
        super().__init__(User, session)
