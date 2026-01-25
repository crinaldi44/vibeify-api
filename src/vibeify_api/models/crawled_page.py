"""Crawled page metadata model.

Stores metadata about HTML crawls persisted in S3.
"""

from datetime import datetime
from typing import Optional

from sqlmodel import Field

from vibeify_api.models.base import BaseModel


class CrawledPage(BaseModel, table=True):
    """Metadata for a crawled URL and its stored HTML."""

    __tablename__ = "crawled_pages"

    id: Optional[int] = Field(default=None, primary_key=True)

    url: str = Field(index=True, max_length=2000)
    data_origin: str = Field(index=True, max_length=200, alias="dataOrigin")
    target_application: Optional[str] = Field(
        default=None,
        index=True,
        max_length=100,
        alias="targetApplication",
    )

    crawled_at: datetime = Field(default_factory=datetime.utcnow, alias="crawledAt")

    content_digest: Optional[str] = Field(
        default=None,
        index=True,
        max_length=200,
        alias="contentDigest",
    )

    s3_key: str = Field(index=True, max_length=500, alias="s3Key")
    s3_bucket: str = Field(max_length=100, alias="s3Bucket")

    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True, alias="userId")

