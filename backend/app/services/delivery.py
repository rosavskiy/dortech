"""Отправка сообщений из outbox: email (SMTP) и webhook (HMAC-SHA256)."""

import json
import logging
import time
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
from pathlib import Path

import aiosmtplib
import httpx
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.security import sign_webhook
from app.models import OutboundKind, OutboundMessage, OutboundStatus, WebhookEndpoint

log = logging.getLogger("delivery")
RETRY_DELAYS = [60, 300, 1800, 7200, 43200, 86400]  # секунды между попытками
TEMPLATES = Environment(
    loader=FileSystemLoader(Path(__file__).resolve().parent.parent / "templates" / "email"),
    autoescape=select_autoescape(["html"]),
)


def render_email(template: str, context: dict) -> tuple[str, str]:
    html = TEMPLATES.get_template(f"{template}.html").render(**context, site_url=settings.site_url)
    try:
        text = TEMPLATES.get_template(f"{template}.txt").render(**context, site_url=settings.site_url)
    except Exception:
        text = "Откройте письмо в почтовом клиенте с поддержкой HTML."
    return html, text


async def send_email(payload: dict) -> None:
    html, text = render_email(payload["template"], payload.get("context", {}))
    msg = EmailMessage()
    msg["From"] = settings.default_from_email
    msg["To"] = ", ".join(payload["to"])
    msg["Subject"] = payload["subject"]
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user or None,
        password=settings.smtp_password or None,
        start_tls=settings.smtp_use_tls,
        timeout=20,
    )


async def send_webhook(message: OutboundMessage, secret: str) -> int:
    body = json.dumps(
        {
            "id": message.delivery_id,
            "event": message.event,
            "created_at": message.created_at.isoformat(),
            "data": message.payload["data"],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode()
    ts = str(int(time.time()))
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Dortech-Webhook/1.0",
        "X-Dortech-Event": message.event or "",
        "X-Dortech-Delivery": message.delivery_id or "",
        "X-Dortech-Timestamp": ts,
        "X-Dortech-Signature": sign_webhook(secret, ts, body),
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(message.payload["url"], content=body, headers=headers)
    return r.status_code


async def process_outbox(limit: int = 50) -> int:
    now = datetime.now(UTC)
    processed = 0
    async with SessionLocal() as session:
        rows = (
            (
                await session.execute(
                    select(OutboundMessage)
                    .where(OutboundMessage.status == OutboundStatus.pending, OutboundMessage.next_attempt_at <= now)
                    .order_by(OutboundMessage.id)
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )
        for m in rows:
            m.attempts += 1
            try:
                if m.kind == OutboundKind.email:
                    await send_email(m.payload)
                    m.status, m.sent_at, m.response_code = OutboundStatus.sent, datetime.now(UTC), 250
                else:
                    secret = settings.webhook_secret
                    if m.endpoint_id:
                        ep = await session.get(WebhookEndpoint, m.endpoint_id)
                        secret = ep.secret if ep else secret
                    code = await send_webhook(m, secret)
                    m.response_code = code
                    if 200 <= code < 300:
                        m.status, m.sent_at = OutboundStatus.sent, datetime.now(UTC)
                    else:
                        raise RuntimeError(f"HTTP {code}")
                m.last_error = None
            except Exception as e:  # noqa: BLE001
                m.last_error = str(e)[:2000]
                if m.attempts > len(RETRY_DELAYS):
                    m.status = OutboundStatus.failed
                    log.error("message %s failed permanently: %s", m.id, e)
                else:
                    m.next_attempt_at = datetime.now(UTC) + timedelta(seconds=RETRY_DELAYS[m.attempts - 1])
                    log.warning("message %s attempt %d failed: %s", m.id, m.attempts, e)
            processed += 1
        await session.commit()
    return processed
