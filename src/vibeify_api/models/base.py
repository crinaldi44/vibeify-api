"""Base model classes using SQLModel."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, func
from sqlmodel import SQLModel, Field


class TimestampMixin(SQLModel):
    """Mixin to add created_at and updated_at timestamp fields."""

    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
    )


class BaseModel(SQLModel, TimestampMixin):
    """Base model with common fields and methods.
    
    Use table=True to create a database table, table=False for API schemas.
    """

    # Note: SQLModel models with table=True become database tables
    # Models without table=True become Pydantic schemas for API validation


class VibeifyModel(BaseModel, table=False):
    """Base model for API schemas (non-table models)."""
    pass
