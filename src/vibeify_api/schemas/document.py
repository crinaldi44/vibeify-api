"""Document schemas."""
import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class DocumentResponse(BaseModel):
    """Document response schema."""

    id: Optional[int] = None
    filename: Optional[str] = None
    original_filename: Optional[str] = None
    file_extension: Optional[str] = None
    content_type: Optional[str] = None
    file_size: Optional[int] = None
    s3_key: Optional[str] = None
    s3_bucket: Optional[str] = None
    uploaded_by_id: Optional[int] = None
    is_active: Optional[bool] = None
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
    upload_url: Optional[str] = None
    s3_key: str

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )
