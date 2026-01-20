from typing import Optional

from sqlmodel import Field

from vibeify_api.models import BaseModel


class Report(BaseModel, table=True):
    __tablename__ = "reports"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    user_id: int = Field(foreign_key="users.id", index=True)
