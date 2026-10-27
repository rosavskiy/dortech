import json
import time

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.security import sign_webhook
from app.models import OutboundKind, OutboundMessage, WebhookDelivery, WebhookEndpoint
from app.services.delivery import send_webhook
from tests.conftest import create_inquiry

pytestmark = pytest.mark.usefixtures("seed")


@pytest.fixture(autouse=True)
def _sink(monkeypatch):
    monkeypatch.setattr(settings, "webhook_sink_enabled", True)
    monkeypatch.setattr(settings, "webhook_secret", "test-secret")
    monkeypatch.setattr(settings, "webhook_url", "")


async def test_sink_validates_signature(client):
    body = json.dumps({"id": "d1", "event": "inquiry.created", "data": {"number": "DT-000001"}}).encode()
    ts = str(int(time.time()))
    ok = await client.post(
        "/api/v1/webhook-sink",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Dortech-Event": "inquiry.created",
            "X-Dortech-Delivery": "d1",
            "X-Dortech-Timestamp": ts,
            "X-Dortech-Signature": sign_webhook("test-secret", ts, body),
        },
    )
    assert ok.status_code == 200 and ok.json()["event"] == "inquiry.created"
    bad = await client.post(
        "/api/v1/webhook-sink",
        content=body + b" ",
        headers={
            "Content-Type": "application/json",
            "X-Dortech-Timestamp": ts,
            "X-Dortech-Signature": sign_webhook("test-secret", ts, body),
        },
    )
    assert bad.status_code == 400
    async with SessionLocal() as s:
        rows = (await s.execute(select(WebhookDelivery).order_by(WebhookDelivery.id))).scalars().all()
        assert [r.signature_valid for r in rows] == [True, False]
        assert rows[0].body["data"]["number"] == "DT-000001"


async def test_inquiry_enqueues_webhook_for_active_endpoint(client, seed):
    async with SessionLocal() as s:
        s.add(
            WebhookEndpoint(
                name="CRM", url="http://sink.local/hook", secret="ep-secret", is_active=True, events=["inquiry.created"]
            )
        )
        s.add(WebhookEndpoint(name="Off", url="http://sink.local/off", secret="x", is_active=False))
        await s.commit()
    await create_inquiry(client, seed["equipment"]["ex-komatsu-pc200"])
    async with SessionLocal() as s:
        hooks = (
            (await s.execute(select(OutboundMessage).where(OutboundMessage.kind == OutboundKind.webhook)))
            .scalars()
            .all()
        )
        assert (
            len(hooks) == 1
            and hooks[0].payload["url"] == "http://sink.local/hook"
            and hooks[0].event == "inquiry.created"
        )
        assert hooks[0].payload["data"]["number"] == "DT-000001" and hooks[0].delivery_id


async def test_send_webhook_signs_request(monkeypatch):
    captured = {}

    class FakeResp:
        status_code = 200

    class FakeClient:
        def __init__(self, *a, **k): ...
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a): ...
        async def post(self, url, content, headers):
            captured.update(url=url, content=content, headers=headers)
            return FakeResp()

    import app.services.delivery as d

    monkeypatch.setattr(d.httpx, "AsyncClient", FakeClient)
    from datetime import UTC, datetime

    msg = OutboundMessage(
        kind=OutboundKind.webhook,
        event="inquiry.created",
        delivery_id="abc",
        payload={"url": "http://x/h", "event": "inquiry.created", "data": {"n": 1}},
        created_at=datetime.now(UTC),
    )
    code = await send_webhook(msg, "s3cret")
    assert code == 200 and captured["url"] == "http://x/h"
    h = captured["headers"]
    assert h["X-Dortech-Signature"] == sign_webhook("s3cret", h["X-Dortech-Timestamp"], captured["content"])
    assert json.loads(captured["content"])["data"] == {"n": 1} and h["X-Dortech-Delivery"] == "abc"
