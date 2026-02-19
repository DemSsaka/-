from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Contribution, Reservation, User, ViewerAccount, Wishlist, WishlistItem

MIN_CONTRIBUTION_CENTS = 100


async def ensure_owner_wishlist(db: AsyncSession, wishlist_id: int, owner_id: int) -> Wishlist:
    wishlist = await db.scalar(
        select(Wishlist).where(Wishlist.id == wishlist_id, Wishlist.owner_id == owner_id)
    )
    if not wishlist:
        raise HTTPException(status_code=404, detail="Wishlist not found")
    return wishlist


async def ensure_owner_item(db: AsyncSession, item_id: int, owner_id: int) -> WishlistItem:
    item = await db.scalar(
        select(WishlistItem)
        .join(Wishlist, Wishlist.id == WishlistItem.wishlist_id)
        .where(WishlistItem.id == item_id, Wishlist.owner_id == owner_id)
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


async def get_wishlist_items_with_aggregates(
    db: AsyncSession, wishlist_id: int, viewer_hash: str | None = None
) -> list[dict]:
    contrib_subq = (
        select(Contribution.item_id, func.coalesce(func.sum(Contribution.amount_cents), 0).label("collected"))
        .where(Contribution.refunded_at.is_(None))
        .group_by(Contribution.item_id)
        .subquery()
    )
    reservation_subq = (
        select(
            Reservation.item_id.label("item_id"),
            Reservation.created_at.label("reserved_at"),
            Reservation.viewer_token_hash.label("reservation_viewer_hash"),
        )
        .where(Reservation.released_at.is_(None))
        .subquery()
    )

    my_contrib_subq = None
    if viewer_hash:
        my_contrib_subq = (
            select(
                Contribution.item_id,
                func.coalesce(func.sum(Contribution.amount_cents), 0).label("mine"),
            )
            .where(Contribution.viewer_token_hash == viewer_hash)
            .where(Contribution.refunded_at.is_(None))
            .group_by(Contribution.item_id)
            .subquery()
        )

    stmt: Select = (
        select(
            WishlistItem,
            func.coalesce(contrib_subq.c.collected, 0).label("collected"),
            reservation_subq.c.reserved_at,
            (reservation_subq.c.reserved_at.is_not(None)).label("reserved"),
            reservation_subq.c.reservation_viewer_hash,
            func.coalesce(my_contrib_subq.c.mine, 0).label("mine") if my_contrib_subq is not None else None,
        )
        .outerjoin(contrib_subq, contrib_subq.c.item_id == WishlistItem.id)
        .outerjoin(reservation_subq, reservation_subq.c.item_id == WishlistItem.id)
        .where(WishlistItem.wishlist_id == wishlist_id)
        .order_by(WishlistItem.position.asc(), WishlistItem.created_at.asc())
    )
    if my_contrib_subq is not None:
        stmt = stmt.outerjoin(my_contrib_subq, my_contrib_subq.c.item_id == WishlistItem.id)

    rows = (await db.execute(stmt)).all()
    result = []
    for row in rows:
        item = row[0]
        collected = int(row[1] or 0)
        reserved_at = row[2]
        reserved = bool(row[3])
        reservation_viewer_hash = row[4]
        mine = int(row[5] or 0) if my_contrib_subq is not None else None
        reserved_by_me = bool(
            viewer_hash
            and reserved
            and reservation_viewer_hash
            and reservation_viewer_hash == viewer_hash
        )
        result.append(
            {
                "item": item,
                "collected": collected,
                "reserved": reserved,
                "reserved_by_me": reserved_by_me,
                "reserved_at": reserved_at,
                "mine": mine,
            }
        )
    return result


async def reserve_item(db: AsyncSession, item: WishlistItem, viewer_hash: str) -> Reservation:
    existing = await db.scalar(
        select(Reservation).where(Reservation.item_id == item.id, Reservation.released_at.is_(None))
    )
    if existing:
        if existing.viewer_token_hash == viewer_hash:
            return existing
        raise HTTPException(status_code=409, detail="Item is already reserved")

    reservation = Reservation(item_id=item.id, viewer_token_hash=viewer_hash)
    db.add(reservation)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Item reservation conflict") from exc
    return reservation


async def unreserve_item(db: AsyncSession, item_id: int, viewer_hash: str) -> None:
    reservation = await db.scalar(
        select(Reservation).where(Reservation.item_id == item_id, Reservation.released_at.is_(None))
    )
    if not reservation:
        raise HTTPException(status_code=404, detail="No active reservation")
    if reservation.viewer_token_hash != viewer_hash:
        raise HTTPException(status_code=403, detail="Only the original reserver can unreserve")
    reservation.released_at = datetime.now(UTC)


async def contribute_to_item(
    db: AsyncSession,
    item: WishlistItem,
    viewer_hash: str,
    amount_cents: int,
    message: str | None,
) -> Contribution:
    if amount_cents < MIN_CONTRIBUTION_CENTS:
        raise HTTPException(
            status_code=422,
            detail=f"Minimum contribution is {MIN_CONTRIBUTION_CENTS} cents",
        )
    if not item.allow_contributions:
        raise HTTPException(status_code=400, detail="Contributions are disabled for this item")

    item_locked = await db.scalar(select(WishlistItem).where(WishlistItem.id == item.id).with_for_update())
    if not item_locked:
        raise HTTPException(status_code=404, detail="Item not found")

    collected = await db.scalar(
        select(func.coalesce(func.sum(Contribution.amount_cents), 0)).where(
            Contribution.item_id == item.id,
            Contribution.refunded_at.is_(None),
        )
    )
    collected = int(collected or 0)
    remaining = item_locked.price_cents - collected
    if remaining <= 0:
        raise HTTPException(status_code=409, detail="Funding goal already reached")
    if amount_cents > remaining:
        raise HTTPException(status_code=422, detail=f"Contribution exceeds remaining amount ({remaining} cents)")

    contribution = Contribution(
        item_id=item.id,
        contributor_user_id=None,
        viewer_token_hash=viewer_hash,
        amount_cents=amount_cents,
        message=message,
    )
    db.add(contribution)
    await db.flush()
    return contribution


async def get_or_create_viewer_account(
    db: AsyncSession, viewer_hash: str, lock_for_update: bool = False
) -> ViewerAccount:
    stmt = select(ViewerAccount).where(ViewerAccount.viewer_token_hash == viewer_hash)
    if lock_for_update:
        stmt = stmt.with_for_update()
    account = await db.scalar(stmt)
    if account:
        return account
    account = ViewerAccount(viewer_token_hash=viewer_hash, balance_cents=100_000)
    db.add(account)
    await db.flush()
    return account


async def refund_item_contributions(db: AsyncSession, item_id: int) -> int:
    contributions = (
        await db.execute(
            select(Contribution)
            .where(Contribution.item_id == item_id, Contribution.refunded_at.is_(None))
            .with_for_update()
        )
    ).scalars().all()
    if not contributions:
        return 0

    refunded_total = 0
    now = datetime.now(UTC)
    for c in contributions:
        refunded_total += c.amount_cents
        refund_usd_cents = c.charged_usd_cents if c.charged_usd_cents > 0 else c.amount_cents
        if c.contributor_user_id:
            user = await db.scalar(select(User).where(User.id == c.contributor_user_id).with_for_update())
            if user:
                user.balance_cents += refund_usd_cents
        else:
            account = await get_or_create_viewer_account(db, c.viewer_token_hash, lock_for_update=True)
            account.balance_cents += refund_usd_cents
        c.refunded_at = now
    return refunded_total
