"""Document schemas."""
import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel


class DocumentResponse(BaseModel):
    """Document response schema."""

    id: int
    filename: str
    original_filename: str
    file_extension: str
    content_type: Optional[str]
    file_size: int
    s3_key: str
    s3_bucket: str
    uploaded_by_id: Optional[int]
    is_active: bool
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    download_url: Optional[str] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )

class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    upload_url: str
    s3_key: str

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )
