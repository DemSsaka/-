from datetime import datetime

from pydantic import BaseModel


class NotificationView(BaseModel):
    id: int
    type: str
    title: str
    body: str | None
    created_at: datetime
    read_at: datetime | None


class NotificationUnreadCount(BaseModel):
    unread: int
