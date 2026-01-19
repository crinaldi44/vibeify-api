"""Document API routes."""
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from querymate import PaginatedResponse, Querymate

from vibeify_api.core.dependencies import get_current_user
from vibeify_api.models.user import User
from vibeify_api.schemas.document import DocumentCreate, DocumentResponse
from vibeify_api.services.document import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_service() -> DocumentService:
    """Dependency to get document service instance."""
    return DocumentService()


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    summary="Create document record and get presigned upload URL",
)
async def create_upload(
    document_data: DocumentCreate,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> dict:
    """Create a document record and get a presigned URL for uploading to S3.
    
    This endpoint creates a document record in the database and returns a presigned
    URL that can be used to upload the file directly to S3. The file should be
    uploaded using a PUT request to the returned URL.
    
    Args:
        document_data: Document metadata (filename, content_type, file_size)
        current_user: Current authenticated user
        service: Document service instance
        
    Returns:
        Dictionary containing:
        - document: Document record
        - upload_url: Presigned URL for uploading
        - s3_key: S3 key where the file will be stored
        
    Example:
        POST /documents/upload
        {
            "filename": "example.pdf",
            "content_type": "application/pdf",
            "file_size": 1024
        }
        
        Response:
        {
            "document": {...},
            "upload_url": "https://s3.amazonaws.com/...",
            "s3_key": "2026/01/18/1/uuid-example.pdf"
        }
    """
    return await service.create_upload(document_data, user_id=current_user.id)


@router.get(
    "",
    summary="List documents with pagination",
    response_model=PaginatedResponse[DocumentResponse],
    description="Get paginated list of documents with QueryMate",
)
async def list_documents(
    query: Querymate = Depends(Querymate.fastapi_dependency),
    service: DocumentService = Depends(get_document_service),
    q: Optional[str] = Query(None, description="Query"),
) -> PaginatedResponse[DocumentResponse]:
    """List documents with pagination metadata.
    
    Query parameters (via QueryMate):
    - `filter`: Filter conditions (e.g., `{"filename": {"like": "%.pdf"}}`)
    - `sort`: Sort fields (e.g., `["-created_at", "filename"]`)
    - `select`: Fields to include
    - `limit`: Maximum records (default: 10, max: 200)
    - `offset`: Skip records (default: 0)
    - `include_pagination`: Include pagination metadata (boolean)
    
    Examples:
    - GET /documents?limit=20&offset=0
    - GET /documents?filter[filename][like]=%.pdf
    - GET /documents?sort=-created_at,filename&limit=10
    """
    return await service.list(query)


@router.get(
    "/{document_id}/download-url",
    summary="Get presigned download URL for a document",
)
async def get_download_url(
    document_id: int,
    service: DocumentService = Depends(get_document_service),
) -> dict:
    """Get a presigned download URL for a specific document.
    
    Args:
        document_id: Document ID
        
    Returns:
        Dictionary with download_url
        
    Raises:
        NotFoundError: If document not found
    """
    url = await service.get_download_url(document_id)
    return {"download_url": url}
