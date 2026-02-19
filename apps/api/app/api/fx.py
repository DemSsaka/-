from datetime import UTC, datetime

from fastapi import APIRouter

from app.services.fx_service import get_usd_rates

router = APIRouter(prefix="/api/fx", tags=["fx"])


@router.get("/rates")
async def get_rates() -> dict:
    rates = await get_usd_rates()
    return {
        "base": "USD",
        "rates": rates,
        "updated_at": datetime.now(UTC).isoformat(),
    }
