from datetime import datetime

from pydantic import BaseModel


class ApiMessage(BaseModel):
    message: str


class RealtimeEvent(BaseModel):
    event_id: str
    type: str
    wishlist_public_id: str
    server_ts: datetime
    data: dict
