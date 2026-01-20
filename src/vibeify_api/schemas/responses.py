"""Error response schemas."""
from typing import TypeVar

from pydantic import ConfigDict
from pydantic.alias_generators import to_camel
from querymate import PaginatedResponse, PaginationInfo

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
