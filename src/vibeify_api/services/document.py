"""Document service for business logic."""
import uuid
from datetime import datetime
from typing import Optional

import aioboto3
from querymate import PaginatedResponse, Querymate

from vibeify_api.core.config import get_settings
from vibeify_api.core.exceptions import NotFoundError, ValidationError
from vibeify_api.models.document import Document
from vibeify_api.schemas.document import DocumentCreate, DocumentResponse
from vibeify_api.services.base import BaseService

settings = get_settings()


class DocumentService(BaseService[Document]):
    """Service for document-related business logic."""

    def __init__(self):
        """Initialize document service."""
        super().__init__(Document)

    def _generate_s3_key(self, filename: str, user_id: Optional[int] = None) -> str:
        """Generate a predictable S3 key for a file.
        
        Format: {year}/{month}/{day}/{user_id}/{uuid}-{filename}
        
        Args:
            filename: Original filename
            user_id: Optional user ID
            
        Returns:
            S3 key string
        """
        now = datetime.utcnow()
        date_prefix = f"{now.year}/{now.month:02d}/{now.day:02d}"
        file_uuid = str(uuid.uuid4())
        
        # Sanitize filename
        safe_filename = filename.replace(" ", "_").replace("/", "_")
        
        if user_id:
            return f"{date_prefix}/{user_id}/{file_uuid}-{safe_filename}"
        return f"{date_prefix}/{file_uuid}-{safe_filename}"

    async def _get_presigned_url(
        self,
        s3_key: str,
        operation: str = "put_object",
        expiration: Optional[int] = None,
    ) -> str:
        """Generate a presigned URL for S3 operations.
        
        Args:
            s3_key: S3 object key
            operation: S3 operation ('put_object' for upload, 'get_object' for download)
            expiration: URL expiration time in seconds (defaults to S3_PRESIGNED_URL_EXPIRATION)
            
        Returns:
            Presigned URL string
        """
        expiration = expiration or settings.S3_PRESIGNED_URL_EXPIRATION
        
        session = aioboto3.Session()
        async with session.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        ) as s3_client:
            if operation == "put_object":
                url = await s3_client.generate_presigned_url(
                    "put_object",
                    Params={"Bucket": settings.S3_BUCKET_NAME, "Key": s3_key},
                    ExpiresIn=expiration,
                )
            else:  # get_object
                url = await s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": settings.S3_BUCKET_NAME, "Key": s3_key},
                    ExpiresIn=expiration,
                )
            return url

    async def create_upload(
        self,
        document_data: DocumentCreate,
        user_id: Optional[int] = None,
    ) -> dict:
        """Create a document record and generate presigned upload URL.
        
        Args:
            document_data: Document creation data
            user_id: Optional user ID who is uploading
            
        Returns:
            Dictionary with document record and presigned upload URL
        """
        # Generate S3 key
        s3_key = self._generate_s3_key(document_data.filename, user_id)
        
        # Create document record
        document = await self.create(
            Document(
                filename=document_data.filename,
                original_filename=document_data.filename,
                content_type=document_data.content_type,
                file_size=document_data.file_size,
                s3_key=s3_key,
                s3_bucket=settings.S3_BUCKET_NAME,
                uploaded_by_id=user_id,
            )
        )
        
        # Generate presigned upload URL
        upload_url = await self._get_presigned_url(s3_key, operation="put_object")
        
        return {
            "document": DocumentResponse.model_validate(document),
            "upload_url": upload_url,
            "s3_key": s3_key,
        }

    async def list(
        self,
        query: Querymate,
    ) -> dict:
        """List documents with pagination.
        
        Args:
            query: QueryMate instance with filters, sort, select, etc.
            
        Returns:
            Paginated response with document instances
        """
        results: PaginatedResponse[Document] = await self.repository.query_paginated(query)
        
        # Add download URLs to each document
        items = []
        for doc in results.items:
            
            # Generate presigned download URL
            try:
                download_url = await self._get_presigned_url(
                    doc.s3_key,
                    operation="get_object",
                )
                doc.download_url = download_url
            except Exception:
                # If URL generation fails, continue without it
                pass
            
            items.append(doc)
        
        # Update results with modified items
        results.items = items
        return results

    async def get_download_url(self, document_id: int) -> str:
        """Get a presigned download URL for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            Presigned download URL
            
        Raises:
            NotFoundError: If document not found
        """
        document = await self.get(document_id)
        if not document:
            raise NotFoundError("Document", document_id)
        
        return await self._get_presigned_url(document.s3_key, operation="get_object")
