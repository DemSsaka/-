import asyncio

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.models import User, Wishlist, WishlistItem
from app.utils.security import hash_password


async def run() -> None:
    async with SessionLocal() as db:
        demo_email = "demo@wishlist.app"
        user = await db.scalar(select(User).where(User.email == demo_email))
        if not user:
            user = User(
                email=demo_email,
                password_hash=hash_password("DemoPass123!"),
                nickname="Demo User",
                balance_cents=100_000,
                theme="light",
            )
            db.add(user)
            await db.flush()

        wishlist = await db.scalar(select(Wishlist).where(Wishlist.owner_id == user.id))
        if not wishlist:
            wishlist = Wishlist(
                owner_id=user.id,
                title="Birthday Wishlist",
                description="A few things I'd love this year",
                currency="USD",
                is_public=True,
            )
            db.add(wishlist)
            await db.flush()

            items = [
                ("Noise-Cancelling Headphones", 29900, True),
                ("Coffee Grinder", 12900, False),
                ("Mechanical Keyboard", 18900, True),
                ("Running Shoes", 9900, False),
                ("Weekend Backpack", 14900, True),
                ("Desk Lamp", 6900, False),
            ]
            for idx, (name, price, contrib) in enumerate(items):
                db.add(
                    WishlistItem(
                        wishlist_id=wishlist.id,
                        name=name,
                        price_cents=price,
                        allow_contributions=contrib,
                        position=idx,
                        notes="Seeded demo item",
                    )
                )

        await db.commit()
        print("Seed complete")
        print("Demo login: demo@wishlist.app / DemoPass123!")
        print(f"Public wishlist id: {wishlist.public_id}")


if __name__ == "__main__":
    asyncio.run(run())
