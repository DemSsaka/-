from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_client_ip, get_current_user, require_viewer_token
from app.db.session import get_db
from app.models.models import Contribution, Notification, OgCache, User, Wishlist, WishlistItem
from app.schemas.public import PublicWishlistSummary
from app.schemas.wishlist import ItemView, WishlistView
from app.services.fx_service import convert_to_usd_cents
from app.services.realtime import publish_event, publish_user_event
from app.services.wishlist_service import (
    contribute_to_item,
    get_wishlist_items_with_aggregates,
    reserve_item,
    unreserve_item,
)
from app.utils.og_parser import parse_og
from app.utils.rate_limit import limiter
from app.utils.security import hash_url

router = APIRouter(prefix="/api", tags=["public"])


@router.get("/public/wishlists", response_model=list[PublicWishlistSummary])
async def list_public_wishlists(db: AsyncSession = Depends(get_db)) -> list[PublicWishlistSummary]:
    stmt = (
        select(Wishlist, User, func.count(WishlistItem.id))
        .outerjoin(
            WishlistItem,
            (WishlistItem.wishlist_id == Wishlist.id) & (WishlistItem.is_archived.is_(False)),
        )
        .join(User, User.id == Wishlist.owner_id)
        .where(Wishlist.is_public.is_(True))
        .group_by(Wishlist.id, User.id)
        .order_by(Wishlist.updated_at.desc())
    )
    rows = (await db.execute(stmt)).all()
    return [
        PublicWishlistSummary(
            public_id=w.public_id,
            title=w.title,
            author_name=(owner.nickname or owner.email),
            currency=w.currency,
            item_count=int(count),
            updated_at=w.updated_at,
        )
        for w, owner, count in rows
    ]


def _map_public_item(data: dict) -> ItemView:
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
        reserved_by_me=data["reserved_by_me"],
        reserved_at=data["reserved_at"],
        collected_cents=data["collected"],
        my_contribution_cents=data["mine"],
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.get("/public/w/{public_id}", response_model=WishlistView)
async def get_public_wishlist(
    public_id: str,
    db: AsyncSession = Depends(get_db),
    viewer_hash: str | None = Depends(require_viewer_token),
) -> WishlistView:
    wishlist = await db.scalar(select(Wishlist).where(Wishlist.public_id == public_id))
    if not wishlist or not wishlist.is_public:
        raise HTTPException(status_code=404, detail="Wishlist not found")

    items = await get_wishlist_items_with_aggregates(db, wishlist.id, viewer_hash)

    return WishlistView(
        id=wishlist.id,
        public_id=wishlist.public_id,
        title=wishlist.title,
        description=wishlist.description,
        currency=wishlist.currency,
        is_public=wishlist.is_public,
        is_owner=False,
        created_at=wishlist.created_at,
        updated_at=wishlist.updated_at,
        items=[_map_public_item(i) for i in items],
    )


@router.post("/public/items/{item_id}/reserve")
async def reserve(
    item_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    viewer_hash: str = Depends(require_viewer_token),
) -> dict:
    ip = get_client_ip(request)
    if not limiter.allow(f"reserve:ip:{ip}", limit=20, window_seconds=60):
        raise HTTPException(status_code=429, detail="Too many reserve attempts")
    if not limiter.allow(f"reserve:viewer:{viewer_hash}", limit=30, window_seconds=60):
        raise HTTPException(status_code=429, detail="Too many reserve attempts")

    item = await db.scalar(select(WishlistItem).where(WishlistItem.id == item_id))
    if not item or item.is_archived:
        raise HTTPException(status_code=404, detail="Item not found")

    wishlist = await db.scalar(select(Wishlist).where(Wishlist.id == item.wishlist_id))
    if not wishlist or not wishlist.is_public:
        raise HTTPException(status_code=404, detail="Wishlist not found")

    reservation = await reserve_item(db, item, viewer_hash)
    await db.commit()
    await publish_event(db, wishlist.public_id, "reservation.changed", {"item_id": item.id})
    return {"reserved": True, "reserved_at": reservation.created_at}


@router.post("/public/items/{item_id}/unreserve")
async def unreserve(
    item_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    viewer_hash: str = Depends(require_viewer_token),
) -> dict:
    ip = get_client_ip(request)
    if not limiter.allow(f"unreserve:ip:{ip}", limit=30, window_seconds=60):
        raise HTTPException(status_code=429, detail="Too many requests")

    item = await db.scalar(select(WishlistItem).where(WishlistItem.id == item_id))
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    wishlist = await db.scalar(select(Wishlist).where(Wishlist.id == item.wishlist_id))
    if not wishlist:
        raise HTTPException(status_code=404, detail="Wishlist not found")

    await unreserve_item(db, item_id, viewer_hash)
    await db.commit()
    await publish_event(db, wishlist.public_id, "reservation.changed", {"item_id": item.id})
    return {"reserved": False}


@router.post("/public/items/{item_id}/contribute")
async def contribute(
    item_id: int,
    body: dict,
    request: Request,
    db: AsyncSession = Depends(get_db),
    viewer_hash: str = Depends(require_viewer_token),
    current_user: User = Depends(get_current_user),
) -> dict:
    honeypot = body.get("honeypot", "")
    if honeypot:
        raise HTTPException(status_code=400, detail="Bot detected")

    amount_cents = int(body.get("amount_cents", 0))
    message = body.get("message")

    ip = get_client_ip(request)
    if not limiter.allow(f"contribute:ip:{ip}", limit=25, window_seconds=60):
        raise HTTPException(status_code=429, detail="Too many contribution attempts")

    item = await db.scalar(select(WishlistItem).where(WishlistItem.id == item_id))
    if not item or item.is_archived:
        raise HTTPException(status_code=404, detail="Item not found")

    wishlist = await db.scalar(select(Wishlist).where(Wishlist.id == item.wishlist_id))
    if not wishlist or not wishlist.is_public:
        raise HTTPException(status_code=404, detail="Wishlist not found")

    contribution = await contribute_to_item(db, item, viewer_hash, amount_cents, message)
    try:
        charged_usd_cents = await convert_to_usd_cents(amount_cents, wishlist.currency)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    contribution.charged_usd_cents = charged_usd_cents
    user_locked = await db.scalar(select(User).where(User.id == current_user.id).with_for_update())
    if not user_locked:
        raise HTTPException(status_code=401, detail="User not found")
    if user_locked.balance_cents < charged_usd_cents:
        raise HTTPException(status_code=422, detail="Insufficient balance")
    user_locked.balance_cents -= charged_usd_cents
    contribution.contributor_user_id = user_locked.id
    contributor_user_id = user_locked.id

    if wishlist.owner_id and (contributor_user_id is None or contributor_user_id != wishlist.owner_id):
        db.add(
            Notification(
                user_id=wishlist.owner_id,
                wishlist_id=wishlist.id,
                item_id=item.id,
                type="contribution.received",
                title=f"Новый вклад в \"{item.name}\"",
                body=(
                    f"Someone contributed {amount_cents / 100:.2f} {wishlist.currency}"
                    + (f". Comment: {message}" if message else ". Без комментария.")
                ),
            )
        )
        await publish_user_event(db, wishlist.owner_id, "notifications.updated", {"increment": 1})

    total = await db.scalar(
        select(func.coalesce(func.sum(Contribution.amount_cents), 0)).where(
            Contribution.item_id == item.id,
            Contribution.refunded_at.is_(None),
        )
    )
    mine = await db.scalar(
        select(func.coalesce(func.sum(Contribution.amount_cents), 0)).where(
            Contribution.item_id == item.id,
            Contribution.viewer_token_hash == viewer_hash,
            Contribution.refunded_at.is_(None),
        )
    )

    await db.commit()
    if contributor_user_id is not None:
        await publish_user_event(db, contributor_user_id, "balance.updated", {"delta_cents": -charged_usd_cents})
    await publish_event(db, wishlist.public_id, "contribution.changed", {"item_id": item.id})

    return {
        "ok": True,
        "contribution_id": contribution.id,
        "collected_cents": int(total or 0),
        "my_contribution_cents": int(mine or 0),
    }


@router.post("/og/parse")
async def parse_og_endpoint(
    payload: dict,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    ip = get_client_ip(request)
    if not limiter.allow(f"og:ip:{ip}", limit=15, window_seconds=60):
        raise HTTPException(status_code=429, detail="Too many parse requests")

    url = str(payload.get("url", "")).strip()
    if not url:
        raise HTTPException(status_code=422, detail="URL is required")

    url_hash = hash_url(url)
    now = datetime.utcnow()

    cached = await db.scalar(select(OgCache).where(OgCache.url_hash == url_hash))
    if cached and cached.fetched_at > now - timedelta(hours=24):
        return {
            "title": cached.title,
            "image_url": cached.image_url,
            "price_cents": cached.price_cents,
            "currency": cached.currency,
            "raw": cached.raw_json,
            "cached": True,
        }

    try:
        parsed = await parse_og(url)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Unable to parse URL metadata: {exc}") from exc

    if cached:
        cached.title = parsed["title"]
        cached.image_url = parsed["image_url"]
        cached.price_cents = parsed["price_cents"]
        cached.currency = parsed["currency"]
        cached.raw_json = parsed["raw"]
        cached.fetched_at = now
    else:
        db.add(
            OgCache(
                url=url,
                url_hash=url_hash,
                title=parsed["title"],
                image_url=parsed["image_url"],
                price_cents=parsed["price_cents"],
                currency=parsed["currency"],
                raw_json=parsed["raw"],
                fetched_at=now,
            )
        )

    await db.commit()
    parsed["cached"] = False
    return parsed
