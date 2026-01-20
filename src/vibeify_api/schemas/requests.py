from pydantic import ConfigDict, Field
from pydantic.alias_generators import to_camel
from querymate.core.config import settings
from querymate.core.querymate import Querymate, GroupByParam, JoinType


class ListQueryParams(Querymate):
    include_pagination: bool = Field(
        default=settings.DEFAULT_RETURN_PAGINATION,
        description="Include pagination metadata in response",
    )
    group_by: GroupByParam | None = Field(
        default=None,
        description="Group results by field. Can be a string or dict with field, granularity, tz_offset/timezone",
    )
    join_type: JoinType | None = Field(
        default=None,
        description="Join type for relationship queries. Options: 'inner' (default), 'left', 'outer'",
    )

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        extra="ignore"
    )