"""Error response schemas."""
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standardized error response format."""

    error: str
    status_code: int
    detail: str | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Resource not found",
                "status_code": 404,
                "detail": "User with ID 123 not found",
            }
        }
