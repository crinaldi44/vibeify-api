from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ValidationErrorDetail(BaseModel):
    """Detailed information about a specific validation error."""
    field: str
    message: str
    type: str
    location: List[str]

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="A human-readable error category or summary.")
    status_code: int = Field(...)
    detail: Optional[str] = Field(None, description="Detailed technical message or trace.")
    messages: Optional[List[ValidationErrorDetail]] = Field(
        default_factory=list,
        description="List of specific validation or logic error messages."
    )

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )
