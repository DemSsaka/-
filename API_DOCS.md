# API Docs

Base URL: `http://localhost:8000`

## Auth
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/auth/me`
  - returns profile-aware fields: `nickname`, `avatar_url`, `theme`, `balance_cents`, `email_verified`
- `GET /api/auth/google/start`
- `GET /api/auth/google/callback`

## Profile
- `GET /api/profile/me`
- `PATCH /api/profile/me`
  - editable fields: `nickname`, `avatar_url`, `bio`, `birth_date`, `theme`

## Uploads
- `POST /api/uploads/image`
  - auth required
  - `multipart/form-data`, field: `file`
  - supported: `jpg`, `jpeg`, `png`, `webp`, `gif` (max 5MB)
  - returns `{ "url": "https://.../uploads/<file>" }`

Cookies:
- `access_token` (HttpOnly)
- `refresh_token` (HttpOnly)

## Owner endpoints
- `GET /api/wishlists`
- `POST /api/wishlists`
- `GET /api/wishlists/{wishlist_id}`
- `PATCH /api/wishlists/{wishlist_id}`
- `DELETE /api/wishlists/{wishlist_id}`
- `POST /api/wishlists/{wishlist_id}/items`
- `PATCH /api/items/{item_id}`
- `DELETE /api/items/{item_id}`
- `POST /api/wishlists/{wishlist_id}/items/reorder`

## Public endpoints
Requires header:
- `X-Viewer-Token: <uuid-like token>`

Routes:
- `GET /api/public/wishlists`
- `GET /api/public/w/{public_id}`
- `POST /api/public/items/{item_id}/reserve`
- `POST /api/public/items/{item_id}/unreserve`
- `POST /api/public/items/{item_id}/contribute`
  - auth required (anonymous contributions are blocked)

`GET /api/public/w/{public_id}` item payload includes:
- `reserved_by_me: boolean` (true only for current viewer token)

Balance behavior:
- Authenticated users start with demo balance `$1000`.
- Balance is stored internally in USD cents.
- Contribution deducts from the contributor balance using live FX conversion from wishlist currency to USD.
- If owner archives/deletes an item with active contributions, contributions are refunded to contributor balances.

## FX
- `GET /api/fx/rates`
  - base: `USD`
  - rates: `USD`, `EUR`, `GBP`, `RUB`

`GET /api/public/wishlists` now includes:
- `author_name: string`

## Notifications
- `GET /api/notifications`
- `GET /api/notifications/unread-count`
- `POST /api/notifications/read-all`
- `DELETE /api/notifications` (clear all)

Created when:
- someone contributes to your wishlist item
- self-contributions to your own wishlist do not generate notifications

## OG parser
- `POST /api/og/parse`

Body:
```json
{ "url": "https://example.com/product" }
```

Returns parsed metadata and `cached` flag.

## WebSocket
- `GET /ws/wishlist/{public_id}`
- `GET /ws/notifications` (auth required, for unread counter/profile updates)

Event schema:
```json
{
  "event_id": "uuid",
  "type": "reservation.changed",
  "wishlist_public_id": "uuid",
  "server_ts": "ISO8601",
  "data": { "item_id": 123 }
}
```

Event types:
- `wishlist.updated`
- `items.reordered`
- `item.updated`
- `item.archived`
- `reservation.changed`
- `contribution.changed`
