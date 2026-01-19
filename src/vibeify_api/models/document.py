"""Document model."""
from typing import Optional

from sqlmodel import Field

from vibeify_api.models.base import BaseModel


class Document(BaseModel, table=True):
    """Document model representing uploaded files."""

    __tablename__ = "documents"

    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(max_length=255, index=True)
    original_filename: str = Field(max_length=255)
    content_type: Optional[str] = Field(default=None, max_length=100)
    file_size: int = Field(default=0)
    s3_key: str = Field(unique=True, index=True, max_length=500)
    s3_bucket: str = Field(max_length=100)
    uploaded_by_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    is_active: bool = Field(default=True, index=True)
