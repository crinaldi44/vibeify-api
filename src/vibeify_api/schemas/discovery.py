from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class DiscoveryRequest(BaseModel):
    urls: list[str] = Field(min_length=1, description="URLs to fetch via Common Crawl")
    data_origin: str = Field(min_length=1, max_length=200, alias="dataOrigin")
    target_application: Optional[str] = Field(
        default=None,
        max_length=100,
        alias="targetApplication",
        description="Optional target application identifier",
    )
    crawl: str = Field(default="CC-MAIN-2025-51", description="Common Crawl crawl id (e.g. CC-MAIN-2025-51)")

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
