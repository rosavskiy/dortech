"""Очередь исходящих сообщений (email, webhook). Запись — в транзакции с бизнес-операцией,
отправка — воркером app.worker."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import OutboundKind, OutboundMessage, OutboundStatus, WebhookEndpoint


def enqueue_email(session: AsyncSession, to: list[str] | str, subject: str, template: str, context: dict) -> None:
    recipients = [to] if isinstance(to, str) else [t for t in to if t]
    if not recipients:
        return
    session.add(
        OutboundMessage(
            kind=OutboundKind.email,
            payload={"to": recipients, "subject": subject, "template": template, "context": context},
            status=OutboundStatus.pending,
            next_attempt_at=datetime.now(UTC),
        )
    )


async def enqueue_webhook(session: AsyncSession, event: str, data: dict) -> None:
    endpoints = (
        (await session.execute(select(WebhookEndpoint).where(WebhookEndpoint.is_active.is_(True)))).scalars().all()
    )
    targets: list[tuple[int | None, str, str]] = [
        (ep.id, ep.url, ep.secret) for ep in endpoints if not ep.events or event in ep.events
    ]
    if settings.webhook_url and settings.webhook_secret:
        targets.append((None, settings.webhook_url, settings.webhook_secret))
    for endpoint_id, url, _secret in targets:
        session.add(
            OutboundMessage(
                kind=OutboundKind.webhook,
                endpoint_id=endpoint_id,
                event=event,
                delivery_id=str(uuid.uuid4()),
                payload={"url": url, "event": event, "data": data},
                status=OutboundStatus.pending,
                next_attempt_at=datetime.now(UTC),
            )
        )
