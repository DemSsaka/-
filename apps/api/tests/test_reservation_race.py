import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.models import User, Wishlist, WishlistItem
from app.services.wishlist_service import reserve_item
from app.utils.security import hash_password, hash_viewer_token


@pytest.mark.asyncio
async def test_reservation_race_condition(db_session: AsyncSession) -> None:
    user = User(email="race@test.com", password_hash=hash_password("Password123!"))
    db_session.add(user)
    await db_session.flush()

    wishlist = Wishlist(owner_id=user.id, title="Race", currency="USD")
    db_session.add(wishlist)
    await db_session.flush()

    item = WishlistItem(wishlist_id=wishlist.id, name="Item", price_cents=1000, position=0)
    db_session.add(item)
    await db_session.commit()

    session_maker = async_sessionmaker(
        bind=db_session.bind, class_=AsyncSession, expire_on_commit=False
    )

    async def do_reserve(token: str) -> bool:
        async with session_maker() as session:
            item_local = await session.get(WishlistItem, item.id)
            if not item_local:
                return False
            viewer_hash = hash_viewer_token(token)
            try:
                await reserve_item(session, item_local, viewer_hash)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                return False

    result1, result2 = await asyncio.gather(do_reserve("viewer-a-token-123456"), do_reserve("viewer-b-token-123456"))
    assert (result1, result2).count(True) == 1
