import pytest

from app.services import fx_service


@pytest.mark.anyio
async def test_convert_to_usd_cents_rub(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_rates() -> dict[str, float]:
        return {"USD": 1.0, "EUR": 0.9, "GBP": 0.8, "RUB": 80.0}

    monkeypatch.setattr(fx_service, "get_usd_rates", fake_rates)
    usd_cents = await fx_service.convert_to_usd_cents(1000, "RUB")
    assert usd_cents == 12
