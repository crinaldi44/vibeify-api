"""Error response schemas."""
from __future__ import annotations

from typing import TypeVar, Optional, Any

from pydantic import ConfigDict, BaseModel, Field
from pydantic.alias_generators import to_camel
from querymate import PaginatedResponse, PaginationInfo

from vibeify_api.schemas.discovery import ProviderDiscoveryError, ProviderSearchResult

T = TypeVar("T")

class ListResponsePaginationInfo(PaginationInfo):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )

class ListResponse[T](PaginatedResponse[T]):
    """Custom paginated response schema."""
    pagination: ListResponsePaginationInfo

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )


class ProviderDiscoveryResponse(BaseModel):
    results: list[ProviderDiscoveryResult]

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ProviderDiscoveryResult(BaseModel):
    provider: str
    results: list[ProviderSearchResult] = Field(default_factory=list)
    error: Optional[ProviderDiscoveryError] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


