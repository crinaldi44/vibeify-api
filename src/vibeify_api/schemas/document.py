"""Document schemas."""
import datetime
from typing import Optional

from pydantic import BaseModel, Field

from vibeify_api.models.document import Document


class DocumentResponse(BaseModel):
    """Document response schema."""

    id: int
    filename: str
    original_filename: str
    content_type: Optional[str]
    file_size: int
    s3_key: str
    s3_bucket: str
    uploaded_by_id: Optional[int]
    is_active: bool
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    download_url: Optional[str] = None  # Presigned URL for download

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class DocumentCreate(BaseModel):
    """Document creation schema."""

    filename: str = Field(..., max_length=255, description="Original filename")
    content_type: Optional[str] = Field(None, max_length=100, description="MIME type")
    file_size: int = Field(..., ge=0, description="File size in bytes")
