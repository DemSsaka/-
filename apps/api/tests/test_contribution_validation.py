import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import User, Wishlist, WishlistItem
from app.services.wishlist_service import contribute_to_item
from app.utils.security import hash_password, hash_viewer_token


@pytest.mark.asyncio
async def test_contribution_rules(db_session: AsyncSession) -> None:
    user = User(email="c@test.com", password_hash=hash_password("Password123!"))
    db_session.add(user)
    await db_session.flush()

    wishlist = Wishlist(owner_id=user.id, title="Contrib", currency="USD")
    db_session.add(wishlist)
    await db_session.flush()

    item = WishlistItem(
        wishlist_id=wishlist.id,
        name="Big Gift",
        price_cents=500,
        allow_contributions=True,
        position=0,
    )
    db_session.add(item)
    await db_session.commit()

    viewer = hash_viewer_token("viewer-c-token-123456")

    with pytest.raises(HTTPException):
        await contribute_to_item(db_session, item, viewer, 0, None)

    with pytest.raises(HTTPException):
        await contribute_to_item(db_session, item, viewer, 99, None)

    ok = await contribute_to_item(db_session, item, viewer, 500, "full")
    assert ok.amount_cents == 500
    await db_session.commit()

    with pytest.raises(HTTPException):
        await contribute_to_item(db_session, item, viewer, 100, None)
