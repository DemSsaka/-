import json
import uuid
from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ws.manager import manager


async def publish_event(db: AsyncSession, public_id: str, event_type: str, data: dict) -> None:
    event = {
        "event_id": str(uuid.uuid4()),
        "type": event_type,
        "wishlist_public_id": public_id,
        "server_ts": datetime.now(UTC).isoformat(),
        "data": data,
    }
    await manager.broadcast(public_id, event)
    payload = json.dumps(event)
    await db.execute(text("SELECT pg_notify('wishlist_events', :payload)"), {"payload": payload})


async def publish_user_event(db: AsyncSession, user_id: int, event_type: str, data: dict) -> None:
    event = {
        "event_id": str(uuid.uuid4()),
        "type": event_type,
        "user_id": user_id,
        "server_ts": datetime.now(UTC).isoformat(),
        "data": data,
    }
    room = f"user:{user_id}"
    await manager.broadcast(room, event)
    payload = json.dumps(event)
    await db.execute(text("SELECT pg_notify('user_events', :payload)"), {"payload": payload})
