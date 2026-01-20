from typing import Optional

from sqlmodel import Field

from vibeify_api.models import BaseModel
from vibeify_api.models.enums import NotificationType


class Notification(BaseModel, table=True):
    __tablename__ = "notifications"

    id: Optional[int] = Field(default=None, primary_key=True)
    message: Optional[str] = None
    notification_type: NotificationType = Field(default=NotificationType.GENERAL)
    user_id: int = Field(foreign_key="users.id", index=True)
