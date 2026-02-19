from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

CurrencyLiteral = Literal["USD", "EUR", "GBP", "RUB"]


class WishlistCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    currency: CurrencyLiteral = "USD"
    is_public: bool = True


class WishlistUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    currency: CurrencyLiteral | None = None
    is_public: bool | None = None


class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    url: HttpUrl | None = None
    image_url: HttpUrl | None = None
    price_cents: int = Field(gt=0, le=100_000_000)
    allow_contributions: bool = False
    notes: str | None = Field(default=None, max_length=2000)


class ItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    url: HttpUrl | None = None
    image_url: HttpUrl | None = None
    price_cents: int | None = Field(default=None, gt=0, le=100_000_000)
    allow_contributions: bool | None = None
    notes: str | None = Field(default=None, max_length=2000)
    is_archived: bool | None = None


class ItemReorder(BaseModel):
    item_ids: list[int]


class ItemView(BaseModel):
    id: int
    name: str
    url: str | None
    image_url: str | None
    price_cents: int
    allow_contributions: bool
    notes: str | None
    position: int
    is_archived: bool
    reserved: bool
    reserved_by_me: bool = False
    reserved_at: datetime | None
    collected_cents: int
    my_contribution_cents: int | None = None
    created_at: datetime
    updated_at: datetime


class WishlistView(BaseModel):
    id: int
    public_id: str
    title: str
    description: str | None
    currency: CurrencyLiteral
    is_public: bool
    is_owner: bool
    created_at: datetime
    updated_at: datetime
    items: list[ItemView]


class WishlistSummary(BaseModel):
    id: int
    public_id: str
    title: str
    currency: CurrencyLiteral
    is_public: bool
    item_count: int
    created_at: datetime
