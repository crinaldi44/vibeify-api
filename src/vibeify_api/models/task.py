import datetime
from typing import Optional

from sqlmodel import Field

from vibeify_api.models import BaseModel
from vibeify_api.models.enums import TaskType


class Task(BaseModel, table=True):

    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    task_name: str
    task_description: str
    task_type: TaskType = Field(default=TaskType.GENERAL_TASK)
    completed_datetime: Optional[datetime.datetime] = Field(default=None)
    target_app: Optional[str] = Field(default=None, max_length=100)
    lockDatetime: Optional[datetime.datetime]
