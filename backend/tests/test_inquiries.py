import pytest
from sqlalchemy import select

from app.core.db import SessionLocal
from app.models import Inquiry, OutboundMessage
from tests.conftest import create_inquiry

pytestmark = pytest.mark.usefixtures("seed")


async def test_public_inquiry_created_with_number_history_and_outbox(client, seed):
    d = await create_inquiry(
        client, seed["equipment"]["ex-komatsu-pc200"], period_from="2026-11-10", period_to="2026-11-11"
    )
    assert d["number"] == "DT-000001" and d["status"] == "new" and d["estimate"]["total"] == "20000"
    async with SessionLocal() as s:
        inq = (await s.execute(select(Inquiry))).scalar_one()
        assert inq.number == "DT-000001" and inq.organization_id is None and inq.estimate_snapshot["total"] == "20000"
        await s.refresh(inq, ["items", "status_history"])
        assert len(inq.items) == 1 and inq.items[0].line_total == 20000
        assert [h.to_status.value for h in inq.status_history] == ["new"]
        kinds = sorted(
            (m.kind.value, m.payload.get("template")) for m in (await s.execute(select(OutboundMessage))).scalars()
        )
        assert ("email", "inquiry_created_client") in kinds and ("email", "inquiry_created_manager") in kinds


async def test_honeypot_and_consent(client, seed):
    base = {
        "items": [{"equipment_id": seed["equipment"]["ex-komatsu-pc200"]}],
        "extra_service_ids": [],
        "contact_name": "Бот",
        "contact_phone": "123456",
    }
    assert (
        await client.post("/api/v1/inquiries", json={**base, "consent": True, "website": "spam"})
    ).status_code == 400
    assert (await client.post("/api/v1/inquiries", json={**base, "consent": False})).status_code == 422


async def test_unpublished_equipment_rejected(client, seed):
    body = {
        "items": [{"equipment_id": seed["equipment"]["ex-hidden"]}],
        "extra_service_ids": [],
        "contact_name": "Тест",
        "contact_phone": "123456",
        "consent": True,
    }
    assert (await client.post("/api/v1/inquiries", json=body)).status_code == 400


async def test_contact_message(client):
    r = await client.post(
        "/api/v1/contact-messages", json={"name": "Иван", "text": "Вопрос по аренде", "consent": True}
    )
    assert r.status_code == 201
