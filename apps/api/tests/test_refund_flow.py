import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Contribution, User, ViewerAccount, Wishlist, WishlistItem
from app.services.wishlist_service import get_or_create_viewer_account, refund_item_contributions


@pytest.mark.anyio
async def test_refund_returns_money_to_viewer_balance(db_session: AsyncSession) -> None:
    user = User(email="owner@example.com", password_hash="x")
    db_session.add(user)
    await db_session.flush()

    wishlist = Wishlist(owner_id=user.id, title="Test", currency="USD", is_public=True)
    db_session.add(wishlist)
    await db_session.flush()

    item = WishlistItem(
        wishlist_id=wishlist.id,
        name="Gift",
        price_cents=10_000,
        allow_contributions=True,
        position=0,
    )
    db_session.add(item)
    await db_session.flush()

    viewer_hash = "viewer_hash_123"
    account = await get_or_create_viewer_account(db_session, viewer_hash, lock_for_update=False)
    account.balance_cents = 95_000

    db_session.add(
        Contribution(
            item_id=item.id,
            viewer_token_hash=viewer_hash,
            amount_cents=5_000,
            message=None,
        )
    )
    await db_session.commit()

    refunded = await refund_item_contributions(db_session, item.id)
    await db_session.commit()
    assert refunded == 5_000

    updated_account = await db_session.scalar(
        select(ViewerAccount).where(ViewerAccount.viewer_token_hash == viewer_hash)
    )
    assert updated_account is not None
    assert updated_account.balance_cents == 100_000

    contribution = await db_session.scalar(select(Contribution).where(Contribution.item_id == item.id))
    assert contribution is not None
    assert contribution.refunded_at is not None
