"""Crawled page schemas."""

import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CrawledPageResponse(BaseModel):
    id: Optional[int] = None
    url: str
    data_origin: str
    target_application: Optional[str] = None
    crawled_at: datetime.datetime
    content_digest: Optional[str] = None
    s3_key: str
    s3_bucket: str
    user_id: Optional[int] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

