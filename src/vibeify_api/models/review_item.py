import datetime
from typing import Optional

from pydantic import ConfigDict
from pydantic.alias_generators import to_camel
from sqlmodel import Field

from vibeify_api.models import BaseModel
from vibeify_api.models.enums import ReviewItemType


class ReviewItem(BaseModel, table=True):

    __tablename__ = "review_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    name: str
    description: str
    review_item_type: ReviewItemType = Field(default=ReviewItemType.GENERAL)
    completed_datetime: Optional[datetime.datetime] = Field(default=None)
    target_app: Optional[str] = Field(default=None, max_length=100)
    lock_datetime: Optional[datetime.datetime]

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )
