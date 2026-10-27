from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import (
    STATUS_LABELS,
    Inquiry,
    InquiryExtraService,
    InquiryItem,
    InquirySource,
    InquiryStatus,
    InquiryStatusHistory,
    Organization,
    User,
)
from app.schemas.inquiries import EstimateOut, InquiryCreateIn
from app.services import outbox
from app.services.pricing import estimate


def inquiry_number(pk: int) -> str:
    return f"DT-{pk:06d}"


async def create_inquiry(
    session: AsyncSession,
    data: InquiryCreateIn,
    *,
    user: User | None = None,
    ip: str | None = None,
    source: InquirySource = InquirySource.web,
) -> tuple[Inquiry, EstimateOut]:
    est = await estimate(session, data)
    if not est.lines:
        raise ValueError("В заявке нет доступных позиций техники")

    organization: Organization | None = user.organization if user and user.organization_id else None
    parent_id: int | None = None
    if data.parent_public_id and user is not None:
        parent = (
            await session.execute(select(Inquiry).where(Inquiry.public_id == data.parent_public_id))
        ).scalar_one_or_none()
        if parent and organization and parent.organization_id == organization.id:
            parent_id = parent.id
            source = InquirySource.repeat

    inquiry = Inquiry(
        organization_id=organization.id if organization else None,
        created_by_id=user.id if user else None,
        contact_name=data.contact_name.strip(),
        contact_phone=data.contact_phone.strip(),
        contact_email=(data.contact_email or (user.email if user else None)),
        company_name_raw=(data.company_name or (organization.name if organization else None)),
        period_from=data.period_from,
        period_to=data.period_to,
        work_place=data.work_place,
        comment=data.comment,
        status=InquiryStatus.new,
        estimated_total=est.total if not est.is_partial else None,
        estimate_snapshot=est.model_dump(mode="json"),
        source=source,
        parent_id=parent_id,
        ip=ip,
    )
    session.add(inquiry)
    await session.flush()
    inquiry.number = inquiry_number(inquiry.id)

    for line in est.lines:
        session.add(
            InquiryItem(
                inquiry_id=inquiry.id,
                equipment_id=line.equipment_id,
                name_snapshot=line.name,
                model_snapshot=line.model,
                quantity=line.quantity,
                units=line.units,
                unit=line.unit,
                unit_price_snapshot=line.unit_price,
                line_total=line.line_total,
                needs_quote=line.needs_quote,
            )
        )
    for extra in est.extras:
        session.add(
            InquiryExtraService(
                inquiry_id=inquiry.id, service_id=extra.id, name_snapshot=extra.name, price_snapshot=extra.price
            )
        )
    session.add(
        InquiryStatusHistory(
            inquiry_id=inquiry.id,
            from_status=None,
            to_status=InquiryStatus.new,
            changed_by_id=user.id if user else None,
            comment="Заявка создана",
        )
    )
    await session.flush()

    payload = inquiry_payload(inquiry, est)
    if inquiry.contact_email:
        outbox.enqueue_email(
            session,
            inquiry.contact_email,
            f"Заявка {inquiry.number} принята",
            "inquiry_created_client",
            payload,
        )
    if settings.notification_emails:
        outbox.enqueue_email(
            session,
            settings.notification_emails,
            f"Новая заявка {inquiry.number}",
            "inquiry_created_manager",
            payload,
        )
    await outbox.enqueue_webhook(session, "inquiry.created", payload)
    return inquiry, est


def inquiry_payload(inquiry: Inquiry, est: EstimateOut | None = None) -> dict:
    snapshot = est.model_dump(mode="json") if est else (inquiry.estimate_snapshot or {})
    return {
        "public_id": str(inquiry.public_id),
        "number": inquiry.number,
        "status": inquiry.status.value,
        "status_label": STATUS_LABELS[inquiry.status],
        "source": inquiry.source.value,
        "created_at": (inquiry.created_at or datetime.now(UTC)).isoformat(),
        "organization": (
            {"id": inquiry.organization_id, "name": inquiry.company_name_raw} if inquiry.organization_id else None
        ),
        "company_name": inquiry.company_name_raw,
        "contact": {"name": inquiry.contact_name, "phone": inquiry.contact_phone, "email": inquiry.contact_email},
        "period": {
            "from": inquiry.period_from.isoformat() if inquiry.period_from else None,
            "to": inquiry.period_to.isoformat() if inquiry.period_to else None,
        },
        "work_place": inquiry.work_place,
        "comment": inquiry.comment,
        "items": snapshot.get("lines", []),
        "extra_services": snapshot.get("extras", []),
        "estimate": {
            "total": snapshot.get("total"),
            "currency": "RUB",
            "is_partial": snapshot.get("is_partial", False),
            "vat_label": snapshot.get("vat_label"),
        },
        "links": {"manager_url": f"{settings.site_url}/manager/inquiries/{inquiry.public_id}"},
    }


def change_status(
    session: AsyncSession, inquiry: Inquiry, to_status: InquiryStatus, *, actor: User | None, comment: str | None = None
) -> None:
    from_status = inquiry.status
    inquiry.status = to_status
    session.add(
        InquiryStatusHistory(
            inquiry_id=inquiry.id,
            from_status=from_status,
            to_status=to_status,
            changed_by_id=actor.id if actor else None,
            comment=comment,
        )
    )


def money(v: Decimal | None) -> str:
    if v is None:
        return "по запросу"
    return f"{v:,.0f}".replace(",", " ") + " ₽"
