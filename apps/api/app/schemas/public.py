from pydantic import BaseModel, Field
from datetime import datetime

from app.schemas.wishlist import CurrencyLiteral


class ReserveRequest(BaseModel):
    honeypot: str | None = Field(default="", max_length=0)


class ContributionRequest(BaseModel):
    amount_cents: int = Field(ge=1, le=100_000_000)
    message: str | None = Field(default=None, max_length=280)
    honeypot: str | None = Field(default="", max_length=0)


class OgParseRequest(BaseModel):
    url: str = Field(min_length=8, max_length=2048)


class PublicWishlistSummary(BaseModel):
    public_id: str
    title: str
    author_name: str
    currency: CurrencyLiteral
    item_count: int
    updated_at: datetime
