import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Reservation, User, Wishlist, WishlistItem
from app.services.wishlist_service import get_wishlist_items_with_aggregates
from app.utils.security import hash_password, hash_viewer_token


@pytest.mark.asyncio
async def test_reserved_by_me_flag(db_session: AsyncSession) -> None:
    user = User(email="owner@test.com", password_hash=hash_password("Password123!"))
    db_session.add(user)
    await db_session.flush()

    wishlist = Wishlist(owner_id=user.id, title="Test", currency="USD")
    db_session.add(wishlist)
    await db_session.flush()

    item = WishlistItem(wishlist_id=wishlist.id, name="Gift", price_cents=2000, position=0)
    db_session.add(item)
    await db_session.flush()

    viewer_a = hash_viewer_token("viewer-a-token-123456")
    viewer_b = hash_viewer_token("viewer-b-token-123456")

    db_session.add(Reservation(item_id=item.id, viewer_token_hash=viewer_a))
    await db_session.commit()

    rows_for_a = await get_wishlist_items_with_aggregates(db_session, wishlist.id, viewer_a)
    rows_for_b = await get_wishlist_items_with_aggregates(db_session, wishlist.id, viewer_b)

    assert rows_for_a[0]["reserved"] is True
    assert rows_for_a[0]["reserved_by_me"] is True

    assert rows_for_b[0]["reserved"] is True
    assert rows_for_b[0]["reserved_by_me"] is False
