"""Document service for business logic."""
from pathlib import Path
from typing import Optional

from fastapi import UploadFile
from querymate import PaginatedResponse, Querymate

from vibeify_api.core.config import get_settings
from vibeify_api.core.exceptions import NotFoundError, ValidationError
from vibeify_api.models import User
from vibeify_api.models.document import Document
from vibeify_api.repository.s3 import S3Repository
from vibeify_api.schemas.document import DocumentCreate, DocumentResponse
from vibeify_api.services.base import BaseService

settings = get_settings()


class DocumentService(BaseService[Document]):
    """Service for document-related business logic."""

    def __init__(self):
        """Initialize document service."""
        super().__init__(Document)
        self.s3_repo = S3Repository()

    async def create_upload(
        self,
        file: UploadFile
    ) -> dict:
        """Creates a document record from the input file buffer and generates a
        presigned upload URL for upload.
        
        Args:
            document_data: Document creation data

        Returns:
            Dictionary with document record and presigned upload URL
        """
        user: User = self.require_current_user()
        user_id = user.id

        s3_key = self.s3_repo.generate_key(file.filename, user_id)

        file_name = Path(file.filename).stem
        file_ext = Path(file.filename).suffix.lower()

        document = await self.create(
            Document(
                filename=file_name,
                file_extension=file_ext,
                original_filename=file.filename,
                content_type=file.content_type,
                file_size=file.size,
                s3_key=s3_key,
                s3_bucket=self.s3_repo.bucket_name,
                uploaded_by_id=user_id,
            )
        )
        
        upload_url = await self.s3_repo.generate_presigned_url(s3_key, operation="put_object")
        
        return {
            "document": DocumentResponse.model_validate(document),
            "upload_url": upload_url,
            "s3_key": s3_key,
        }

    async def list(
        self,
        query: Querymate,
    ) -> PaginatedResponse[DocumentResponse]:
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
                download_url = await self.s3_repo.generate_presigned_url(
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
        
        return await self.s3_repo.generate_presigned_url(document.s3_key, operation="get_object")
