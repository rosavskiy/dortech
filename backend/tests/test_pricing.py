import pytest

pytestmark = pytest.mark.usefixtures("seed")


async def test_estimate_formula_and_rounding(client, seed):
    e = seed["equipment"]
    body = {
        "items": [{"equipment_id": e["ex-komatsu-pc200"], "quantity": 2, "unit": "shift", "units": 3}],
        "extra_service_ids": [1],
    }
    d = (await client.post("/api/v1/inquiries/estimate", json=body)).json()
    assert d["lines"][0]["line_total"] == "60000" and d["total"] == "75000" and d["is_partial"] is False


async def test_estimate_period_default_units_and_day_rate(client, seed):
    e = seed["equipment"]
    body = {
        "items": [{"equipment_id": e["roller-jcb-vmt"], "quantity": 1, "unit": "day"}],
        "period_from": "2026-11-10",
        "period_to": "2026-11-12",
        "extra_service_ids": [],
    }
    d = (await client.post("/api/v1/inquiries/estimate", json=body)).json()
    assert (
        d["lines"][0]["units"] == 3
        and d["lines"][0]["unit_price"] == "10000.00"
        and d["lines"][0]["line_total"] == "30000"
    )


async def test_estimate_hidden_price_is_quote(client, seed):
    e = seed["equipment"]
    body = {
        "items": [
            {"equipment_id": e["ex-jcb-3cx"], "quantity": 1, "unit": "shift"},
            {"equipment_id": e["roller-jcb-vmt"], "quantity": 1, "unit": "shift"},
        ],
        "extra_service_ids": [],
    }
    d = (await client.post("/api/v1/inquiries/estimate", json=body)).json()
    assert d["is_partial"] is True and d["lines"][0]["needs_quote"] is True and d["total"] == "5000"


async def test_rounding_step(client, seed):
    from decimal import Decimal

    from app.services.pricing import round_money

    assert round_money(Decimal("1234.56"), 1) == Decimal("1235")
    assert round_money(Decimal("1234.56"), 10) == Decimal("1230")
    assert round_money(Decimal("1235"), 10) == Decimal("1240")
    assert round_money(Decimal("1250"), 100) == Decimal("1300")


async def test_estimate_validation(client, seed):
    assert (
        await client.post("/api/v1/inquiries/estimate", json={"items": [], "extra_service_ids": []})
    ).status_code == 422
    too_many = [{"equipment_id": 1}] * 11
    assert (
        await client.post("/api/v1/inquiries/estimate", json={"items": too_many, "extra_service_ids": []})
    ).status_code == 422
