import asyncio
from datetime import UTC, datetime, timedelta

import httpx

SUPPORTED = ("USD", "EUR", "GBP", "RUB")

_cache: dict | None = None
_cache_until: datetime | None = None
_lock = asyncio.Lock()


async def get_usd_rates() -> dict[str, float]:
    global _cache, _cache_until

    now = datetime.now(UTC)
    if _cache and _cache_until and now < _cache_until:
        return _cache

    async with _lock:
        now = datetime.now(UTC)
        if _cache and _cache_until and now < _cache_until:
            return _cache

        params = {
            "from": "USD",
            "to": ",".join([c for c in SUPPORTED if c != "USD"]),
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get("https://api.frankfurter.app/latest", params=params)
                resp.raise_for_status()
                payload = resp.json()
                rates = payload.get("rates", {})
                parsed = {
                    "USD": 1.0,
                    "EUR": float(rates.get("EUR", 0)),
                    "GBP": float(rates.get("GBP", 0)),
                    "RUB": float(rates.get("RUB", 0)),
                }
                if not parsed["EUR"] or not parsed["GBP"] or not parsed["RUB"]:
                    raise ValueError("Incomplete rates response")
                _cache = parsed
                _cache_until = now + timedelta(minutes=15)
                return parsed
        except Exception:
            # Safe fallback if provider is unavailable.
            fallback = {"USD": 1.0, "EUR": 0.92, "GBP": 0.79, "RUB": 76.6}
            _cache = fallback
            _cache_until = now + timedelta(minutes=5)
            return fallback


async def convert_to_usd_cents(amount_cents: int, currency: str) -> int:
    cur = currency.upper()
    if cur == "USD":
        return int(amount_cents)
    rates = await get_usd_rates()
    per_usd = rates.get(cur)
    if not per_usd or per_usd <= 0:
        raise ValueError(f"Unsupported currency conversion: {currency}")
    # amount in target currency / (target per USD) = USD amount
    usd_value = (amount_cents / 100.0) / per_usd
    return int(round(usd_value * 100))
