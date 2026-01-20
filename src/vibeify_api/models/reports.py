import uuid
from typing import Optional

from pydantic import ConfigDict
from pydantic.alias_generators import to_camel
from sqlmodel import Field

from vibeify_api.models import BaseModel


class Report(BaseModel, table=True):

    __tablename__ = "reports"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    user_id: Optional[int] = Field(foreign_key="users.id", index=True)
    document_id: Optional[int] = Field(foreign_key="documents.id", index=True)
    status: str = Field(default="PENDING")
    progress_min: int = Field(default=0)
    progress_max: int = Field(default=100)
    report_uuid: str = Field(default=str(uuid.uuid4()))

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )
