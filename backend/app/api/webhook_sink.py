"""Тестовый приёмник webhook (ТЗ 6 «Обмен данными»): включается WEBHOOK_SINK_ENABLED=1,
проверяет подпись HMAC-SHA256 и сохраняет доставку для просмотра в панели."""

import hmac
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_session
from app.core.security import sign_webhook
from app.models import WebhookDelivery

router = APIRouter(prefix="/webhook-sink", tags=["webhook"])


@router.post("")
async def receive(request: Request, session: AsyncSession = Depends(get_session)) -> dict:
    if not settings.webhook_sink_enabled:
        raise HTTPException(404, "Not found")
    body = await request.body()
    ts = request.headers.get("X-Dortech-Timestamp", "")
    given = request.headers.get("X-Dortech-Signature", "")
    expected = sign_webhook(settings.webhook_secret, ts, body)
    valid = bool(ts) and hmac.compare_digest(given, expected)
    try:
        payload = json.loads(body.decode("utf-8")) if body else None
    except ValueError:
        payload = {"raw": body.decode("utf-8", "replace")[:5000]}
    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower().startswith("x-dortech") or k.lower() in ("content-type", "user-agent")
    }
    session.add(WebhookDelivery(headers=headers, body=payload, signature_valid=valid))
    await session.commit()
    if not valid:
        raise HTTPException(400, "Неверная подпись")
    return {
        "ok": True,
        "event": request.headers.get("X-Dortech-Event"),
        "delivery": request.headers.get("X-Dortech-Delivery"),
    }
