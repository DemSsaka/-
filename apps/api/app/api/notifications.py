from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Notification, User
from app.schemas.common import ApiMessage
from app.schemas.notification import NotificationUnreadCount, NotificationView
from app.services.realtime import publish_user_event

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationView])
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[NotificationView]:
    rows = (
        await db.execute(
            select(Notification)
            .where(Notification.user_id == current_user.id)
            .order_by(Notification.created_at.desc())
            .limit(50)
        )
    ).scalars().all()
    return [
        NotificationView(
            id=n.id,
            type=n.type,
            title=n.title,
            body=n.body,
            created_at=n.created_at,
            read_at=n.read_at,
        )
        for n in rows
    ]


@router.get("/unread-count", response_model=NotificationUnreadCount)
async def unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationUnreadCount:
    unread = await db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.read_at.is_(None),
        )
    )
    return NotificationUnreadCount(unread=int(unread or 0))


@router.post("/read-all", response_model=NotificationUnreadCount)
async def read_all(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationUnreadCount:
    now = datetime.now(UTC)
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.read_at.is_(None))
        .values(read_at=now)
    )
    await publish_user_event(db, current_user.id, "notifications.updated", {"unread": 0})
    await db.commit()
    return NotificationUnreadCount(unread=0)


@router.delete("", response_model=ApiMessage)
async def clear_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiMessage:
    rows = (
        await db.execute(select(Notification).where(Notification.user_id == current_user.id))
    ).scalars().all()
    for row in rows:
        await db.delete(row)
    await publish_user_event(db, current_user.id, "notifications.updated", {"unread": 0})
    await db.commit()
    return ApiMessage(message="Notifications cleared")
