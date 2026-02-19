from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Contribution, Reservation, User, Wishlist, WishlistItem
from app.schemas.common import ApiMessage
from app.schemas.wishlist import (
    ItemCreate,
    ItemReorder,
    ItemUpdate,
    ItemView,
    WishlistCreate,
    WishlistSummary,
    WishlistUpdate,
    WishlistView,
)
from app.services.realtime import publish_event
from app.services.wishlist_service import ensure_owner_item, ensure_owner_wishlist, get_wishlist_items_with_aggregates
from app.services.wishlist_service import refund_item_contributions

router = APIRouter(prefix="/api", tags=["wishlists"])


def map_item_view(data: dict, is_owner: bool) -> ItemView:
    item = data["item"]
    return ItemView(
        id=item.id,
        name=item.name,
        url=item.url,
        image_url=item.image_url,
        price_cents=item.price_cents,
        allow_contributions=item.allow_contributions,
        notes=item.notes,
        position=item.position,
        is_archived=item.is_archived,
        reserved=data["reserved"],
        reserved_by_me=False if is_owner else data["reserved_by_me"],
        reserved_at=data["reserved_at"],
        collected_cents=data["collected"],
        my_contribution_cents=None if is_owner else data["mine"],
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.get("/wishlists", response_model=list[WishlistSummary])
async def list_wishlists(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[WishlistSummary]:
    stmt = (
        select(Wishlist, func.count(WishlistItem.id))
        .outerjoin(WishlistItem, WishlistItem.wishlist_id == Wishlist.id)
        .where(Wishlist.owner_id == user.id)
        .group_by(Wishlist.id)
        .order_by(Wishlist.created_at.desc())
    )
    rows = (await db.execute(stmt)).all()
    return [
        WishlistSummary(
            id=w.id,
            public_id=w.public_id,
            title=w.title,
            currency=w.currency,
            is_public=w.is_public,
            item_count=count,
            created_at=w.created_at,
        )
        for w, count in rows
    ]


@router.post("/wishlists", response_model=WishlistSummary)
async def create_wishlist(
    payload: WishlistCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WishlistSummary:
    wishlist = Wishlist(
        owner_id=user.id,
        title=payload.title,
        description=payload.description,
        currency=payload.currency,
        is_public=payload.is_public,
    )
    db.add(wishlist)
    await db.flush()
    await db.commit()
    return WishlistSummary(
        id=wishlist.id,
        public_id=wishlist.public_id,
        title=wishlist.title,
        currency=wishlist.currency,
        is_public=wishlist.is_public,
        item_count=0,
        created_at=wishlist.created_at,
    )


@router.get("/wishlists/{wishlist_id}", response_model=WishlistView)
async def get_owner_wishlist(
    wishlist_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WishlistView:
    wishlist = await ensure_owner_wishlist(db, wishlist_id, user.id)
    items = await get_wishlist_items_with_aggregates(db, wishlist.id)
    return WishlistView(
        id=wishlist.id,
        public_id=wishlist.public_id,
        title=wishlist.title,
        description=wishlist.description,
        currency=wishlist.currency,
        is_public=wishlist.is_public,
        is_owner=True,
        created_at=wishlist.created_at,
        updated_at=wishlist.updated_at,
        items=[map_item_view(i, is_owner=True) for i in items],
    )


@router.patch("/wishlists/{wishlist_id}", response_model=WishlistView)
async def update_wishlist(
    wishlist_id: int,
    payload: WishlistUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WishlistView:
    wishlist = await ensure_owner_wishlist(db, wishlist_id, user.id)
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(wishlist, key, value)
    await db.commit()
    await publish_event(db, wishlist.public_id, "wishlist.updated", {"wishlist_id": wishlist.id})
    items = await get_wishlist_items_with_aggregates(db, wishlist.id)
    return WishlistView(
        id=wishlist.id,
        public_id=wishlist.public_id,
        title=wishlist.title,
        description=wishlist.description,
        currency=wishlist.currency,
        is_public=wishlist.is_public,
        is_owner=True,
        created_at=wishlist.created_at,
        updated_at=wishlist.updated_at,
        items=[map_item_view(i, is_owner=True) for i in items],
    )


@router.delete("/wishlists/{wishlist_id}", response_model=ApiMessage)
async def delete_wishlist(
    wishlist_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiMessage:
    wishlist = await ensure_owner_wishlist(db, wishlist_id, user.id)
    await db.delete(wishlist)
    await db.commit()
    return ApiMessage(message="Wishlist deleted")


@router.post("/wishlists/{wishlist_id}/items", response_model=ItemView)
async def create_item(
    wishlist_id: int,
    payload: ItemCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ItemView:
    wishlist = await ensure_owner_wishlist(db, wishlist_id, user.id)
    max_pos = await db.scalar(
        select(func.coalesce(func.max(WishlistItem.position), -1)).where(WishlistItem.wishlist_id == wishlist.id)
    )
    item = WishlistItem(
        wishlist_id=wishlist.id,
        name=payload.name,
        url=str(payload.url) if payload.url else None,
        image_url=str(payload.image_url) if payload.image_url else None,
        price_cents=payload.price_cents,
        allow_contributions=payload.allow_contributions,
        notes=payload.notes,
        position=int(max_pos or -1) + 1,
    )
    db.add(item)
    await db.flush()
    await db.commit()
    await publish_event(db, wishlist.public_id, "item.updated", {"item_id": item.id})
    return ItemView(
        id=item.id,
        name=item.name,
        url=item.url,
        image_url=item.image_url,
        price_cents=item.price_cents,
        allow_contributions=item.allow_contributions,
        notes=item.notes,
        position=item.position,
        is_archived=item.is_archived,
        reserved=False,
        reserved_by_me=False,
        reserved_at=None,
        collected_cents=0,
        my_contribution_cents=None,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.patch("/items/{item_id}", response_model=ItemView)
async def update_item(
    item_id: int,
    payload: ItemUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ItemView:
    item = await ensure_owner_item(db, item_id, user.id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        if key in {"url", "image_url"} and value is not None:
            value = str(value)
        setattr(item, key, value)

    await db.commit()

    reserved_row = await db.scalar(
        select(Reservation).where(Reservation.item_id == item.id, Reservation.released_at.is_(None))
    )
    collected = await db.scalar(
        select(func.coalesce(func.sum(Contribution.amount_cents), 0)).where(
            Contribution.item_id == item.id,
            Contribution.refunded_at.is_(None),
        )
    )

    wishlist = await db.scalar(select(Wishlist).where(Wishlist.id == item.wishlist_id))
    if wishlist:
        await publish_event(db, wishlist.public_id, "item.updated", {"item_id": item.id})

    return ItemView(
        id=item.id,
        name=item.name,
        url=item.url,
        image_url=item.image_url,
        price_cents=item.price_cents,
        allow_contributions=item.allow_contributions,
        notes=item.notes,
        position=item.position,
        is_archived=item.is_archived,
        reserved=reserved_row is not None,
        reserved_by_me=False,
        reserved_at=reserved_row.created_at if reserved_row else None,
        collected_cents=int(collected or 0),
        my_contribution_cents=None,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.delete("/items/{item_id}", response_model=ApiMessage)
async def archive_or_delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiMessage:
    item = await ensure_owner_item(db, item_id, user.id)
    has_activity = (
        await db.scalar(
            select(func.count(Contribution.id)).where(Contribution.item_id == item.id, Contribution.refunded_at.is_(None))
        )
    ) or (
        await db.scalar(select(func.count(Reservation.id)).where(Reservation.item_id == item.id))
    )

    wishlist = await db.scalar(select(Wishlist).where(Wishlist.id == item.wishlist_id))
    if not wishlist:
        raise HTTPException(status_code=404, detail="Wishlist not found")

    if has_activity:
        refunded_total = await refund_item_contributions(db, item.id)
        item.is_archived = True
        await db.commit()
        await publish_event(db, wishlist.public_id, "item.archived", {"item_id": item.id})
        await publish_event(db, wishlist.public_id, "contribution.changed", {"item_id": item.id})
        if refunded_total > 0:
            return ApiMessage(message="Item archived. Contributions refunded to contributor balances")
        return ApiMessage(message="Item archived due to existing reservations/contributions")

    await db.delete(item)
    await db.commit()
    await publish_event(db, wishlist.public_id, "item.archived", {"item_id": item_id})
    return ApiMessage(message="Item deleted")


@router.post("/wishlists/{wishlist_id}/items/reorder", response_model=ApiMessage)
async def reorder_items(
    wishlist_id: int,
    payload: ItemReorder,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiMessage:
    wishlist = await ensure_owner_wishlist(db, wishlist_id, user.id)
    items = (
        await db.execute(select(WishlistItem).where(WishlistItem.wishlist_id == wishlist.id))
    ).scalars().all()

    item_map = {item.id: item for item in items}
    if set(payload.item_ids) != set(item_map.keys()):
        raise HTTPException(status_code=422, detail="Reorder payload must include all item IDs")

    for idx, item_id in enumerate(payload.item_ids):
        item_map[item_id].position = idx

    await db.commit()
    await publish_event(db, wishlist.public_id, "items.reordered", {"item_ids": payload.item_ids})
    return ApiMessage(message="Items reordered")
