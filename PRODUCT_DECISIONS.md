# Product Decisions

## 1) Privacy model for reservations and contributions
- Decision: Owner does not see who reserved or who contributed.
- Why: Preserves surprise gifting and avoids social pressure.
- Implementation:
  - `viewer_token` generated client-side for anonymous visitors.
  - Only hashed viewer token stored (`sha256(token + pepper)`).
  - Owner endpoints query aggregate totals/status only.
  - Public users can see "Reserved by someone" and aggregate funding progress.

## 2) Overfunding policy
- Decision: Hard cap at item target (`price_cents`).
- Why: Predictable and avoids accidental overcollection.
- Implementation:
  - Contribution service locks item row (`SELECT ... FOR UPDATE`).
  - Rejects contribution above remaining amount.
  - Returns clear error detail with remaining cents.

## 3) Minimum contribution
- Decision: 100 cents.
- Why: Deters spam and trivial noise while staying accessible.
- Implementation: Validation in backend service and request schema.

## 4) Currency behavior
- Decision: Per-wishlist currency (USD default, EUR/GBP supported).
- Why: Keeps consistency in each list while allowing user preference.
- Implementation:
  - Currency stored in wishlist.
  - All item prices/contributions interpreted in wishlist currency.
  - Frontend uses Intl formatting.

## 5) Item deletion with existing activity
- Decision: Soft archive if item has reservations or contributions.
- Why: Preserves audit/history and prevents data loss.
- Implementation:
  - Delete action checks related rows.
  - If activity exists => `is_archived = true`.
  - Archived items are hidden in public active list and treated as historical.

## 6) Unreserve policy
- Decision: Only same anonymous viewer token can unreserve.
- Why: Prevents griefing and reservation hijacking.
- Implementation:
  - Compare active reservation token hash with caller token hash.
  - Owner cannot unreserve in owner API/UI.

## 7) Empty states
- Owner empty state:
  - CTA to add first item or paste URL metadata.
- Public empty state:
  - Friendly message to check back later.

## 8) Realtime transport and resilience
- Decision: WebSocket first, polling fallback.
- Why: Low latency UX with resilience on unstable networks.
- Implementation:
  - WS endpoint `/ws/wishlist/{public_id}`.
  - Backoff reconnect with jitter and reconnect badge.
  - Automatic polling every 10s while disconnected.

## 9) Abuse prevention
- Decision: lightweight layered controls.
- Why: Good baseline without complex captcha friction.
- Implementation:
  - Sliding-window limits for IP + viewer-token on public mutation routes.
  - Stricter rate limit for OG parse endpoint.
  - Honeypot field rejection for public forms.

## 10) OG metadata ingestion
- Decision: parse with partial-failure handling and cache.
- Why: Product URL metadata quality varies by site.
- Implementation:
  - Parse OG/Twitter + JSON-LD product + title fallback.
  - SSRF hardening blocks internal/private IP targets.
  - 24h DB cache keyed by URL hash.
  - Returns warning for blocked/non-HTML pages.

## 11) Optional private mode
- Decision: supported with `is_public` boolean.
- Why: gives owner control if they want to disable share access.
- Implementation:
  - Public read/mutation endpoints enforce `is_public == true`.

## 12) Accessibility baseline
- Decision: semantic structure + keyboard-friendly controls + status messaging.
- Why: shipping quality requires inclusive defaults.
- Implementation:
  - Proper button/label usage.
  - ARIA live in reconnect status.
  - Color contrast tuned for readability.
