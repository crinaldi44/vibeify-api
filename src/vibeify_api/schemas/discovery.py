from __future__ import annotations

import re
from typing import Optional, Literal, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel
from urllib.parse import urlparse


class DiscoveryRequest(BaseModel):
    urls: list[str] = Field(
        default_factory=list,
        description="Exact URLs to fetch. You may also include wildcard patterns (eg https://example.com/*).",
    )
    seed_url: Optional[str] = Field(
        default=None,
        alias="seedUrl",
        description="Optional central URL/pattern to expand into many concrete URLs (eg https://www.nike.com/*).",
    )
    match_type: Literal["exact", "prefix", "host", "domain"] = Field(
        default="prefix",
        alias="matchType",
        description="Match type used when expanding seed_url or wildcard URLs.",
    )
    max_urls: int = Field(
        default=500,
        ge=1,
        le=10_000,
        alias="maxUrls",
        description="Maximum number of URLs to discover from the Common Crawl index per seed/pattern.",
    )
    page_size: int = Field(
        default=1000,
        ge=1,
        le=5000,
        alias="pageSize",
        description=(
            "Common Crawl CDX paging parameter. Note: this follows PyWB ZipNum semantics "
            "(pageSize is compressed index blocks, not necessarily 'URLs per page')."
        ),
    )
    url_regex: Optional[str] = Field(
        default=None,
        alias="urlRegex",
        description="Optional regex applied to discovered URLs before enqueuing crawl jobs.",
    )
    data_origin: str = Field(min_length=1, max_length=200, alias="dataOrigin")
    target_application: Optional[str] = Field(
        default=None,
        max_length=100,
        alias="targetApplication",
        description="Optional target application identifier",
    )
    crawl: str = Field(default="CC-MAIN-2025-51", description="Common Crawl crawl id (e.g. CC-MAIN-2025-51)")

    @field_validator("urls")
    @classmethod
    def validate_urls_non_empty(cls, urls: list[str]) -> list[str]:
        cleaned = [u.strip() for u in urls if u and u.strip()]
        return cleaned

    @field_validator("url_regex")
    @classmethod
    def validate_url_regex(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f"Invalid urlRegex: {e}") from e
        return v

    @model_validator(mode="after")
    def validate_has_input(self) -> "DiscoveryRequest":
        if not self.urls and not self.seed_url:
            raise ValueError("Provide either urls or seedUrl")

        # Validate basic URL/pattern shapes early so workers don't get garbage.
        candidates = list(self.urls)
        if self.seed_url:
            candidates.append(self.seed_url)

        bad: list[str] = []
        for u in candidates:
            u = (u or "").strip()
            if not u:
                bad.append(u)
                continue
            if u.startswith("*.") and len(u) > 2:
                continue
            if "://" in u:
                parsed = urlparse(u.replace("*", ""))
                if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                    bad.append(u)
                continue
            # Allow bare domains/hosts for host/domain queries (eg nike.com, www.nike.com)
            if "." not in u or " " in u:
                bad.append(u)

        if bad:
            raise ValueError(f"Invalid urls/seedUrl: {bad}")
        return self

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class DiscoveryJobResponse(BaseModel):
    job_id: str

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ProviderDiscoveryError(BaseModel):
    code: str
    message: str
    details: Optional[str] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ProviderDiscoveryRequest(BaseModel):
    """A single provider query request (eg Serper, Amazon, etc.)."""

    provider: str = Field(default="serper", min_length=1, description="Provider identifier (eg 'serper').")
    query: str = Field(min_length=1, description="Free-text query for the provider.")

    search_type: str = Field(
        default="search",
        alias="type",
        description="Provider search type (eg 'search', 'shopping', 'images', 'news', ...).",
    )
    num: int = Field(default=10, ge=1, le=100, description="Number of results to request when supported.")
    page: Optional[int] = Field(default=None, ge=1, description="Optional 1-based page number when supported.")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ProviderSearchResult(BaseModel):
    """Normalized result item across providers."""

    title: Optional[str] = None
    url: str
    snippet: Optional[str] = None
    source: Optional[str] = None
    rank: Optional[int] = None
    result_type: str = Field(default="organic", alias="type")
    extra: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
