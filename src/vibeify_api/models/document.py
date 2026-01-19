"""Document model."""
from typing import Optional

from sqlmodel import Field

from vibeify_api.models.base import BaseModel
from vibeify_api.models.enums import DocumentType


class Document(BaseModel, table=True):
    """Document model representing uploaded files."""

    __tablename__ = "documents"

    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(max_length=255, index=True)
    original_filename: str = Field(max_length=255, alias="originalFilename")
    file_extension: str = Field(max_length=10, alias="fileExtension")
    content_type: Optional[str] = Field(default=None, max_length=100, alias="contentType")
    file_size: int = Field(default=0, alias="fileSize")
    s3_key: str = Field(unique=True, index=True, max_length=500, alias="s3Key")
    s3_bucket: str = Field(max_length=100, alias="s3Bucket")
    uploaded_by_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True, alias="uploadedById")
    is_active: bool = Field(default=True, index=True, alias="isActive")
    document_type: DocumentType = Field(default=DocumentType.USER_UPLOAD, alias="documentType")
