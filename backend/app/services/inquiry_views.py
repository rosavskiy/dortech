"""Сериализация заявок для кабинетов."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    STATUS_LABELS,
    STATUS_TRANSITIONS,
    Attachment,
    Equipment,
    Inquiry,
    InquiryComment,
    InquiryItem,
    InquiryStatusHistory,
    Role,
    User,
)
from app.schemas.account import (
    AttachmentOut,
    CommentOut,
    ExtraOut,
    HistoryOut,
    InquiryBrief,
    InquiryDetail,
    ItemOut,
    UserBrief,
)
from app.services.inquiries import money

INQUIRY_LOAD = (
    selectinload(Inquiry.organization),
    selectinload(Inquiry.assigned_to),
    selectinload(Inquiry.items).selectinload(InquiryItem.equipment),
    selectinload(Inquiry.extra_services),
    selectinload(Inquiry.status_history).selectinload(InquiryStatusHistory.changed_by),
    selectinload(Inquiry.comments).selectinload(InquiryComment.author),
    selectinload(Inquiry.attachments).selectinload(Attachment.uploaded_by),
    selectinload(Inquiry.parent),
)
BRIEF_LOAD = (selectinload(Inquiry.organization), selectinload(Inquiry.assigned_to), selectinload(Inquiry.items))


def user_brief(u: User | None) -> UserBrief | None:
    if u is None:
        return None
    return UserBrief(id=u.id, name=str(u), email=u.email, role=u.role.value)


def brief(i: Inquiry) -> InquiryBrief:
    snap = i.estimate_snapshot or {}
    return InquiryBrief(
        public_id=i.public_id,
        number=i.number or f"#{i.id}",
        status=i.status,
        status_label=STATUS_LABELS[i.status],
        created_at=i.created_at,
        period_from=i.period_from,
        period_to=i.period_to,
        items_count=len(i.items),
        estimated_total=Decimal(str(snap["total"])) if snap.get("total") is not None else i.estimated_total,
        is_partial=bool(snap.get("is_partial")),
        organization=i.organization.name if i.organization else i.company_name_raw,
        contact_name=i.contact_name,
        assigned_to=user_brief(i.assigned_to),
        source=i.source.value,
    )


def detail(i: Inquiry, *, viewer: User) -> InquiryDetail:
    b = brief(i)
    snap = i.estimate_snapshot or {}
    staff = viewer.is_staff
    items = [
        ItemOut(
            equipment_id=it.equipment_id,
            slug=it.equipment.slug if it.equipment else None,
            name=it.name_snapshot,
            model=it.model_snapshot,
            quantity=it.quantity,
            units=it.units,
            unit=it.unit,
            unit_price=it.unit_price_snapshot,
            line_total=it.line_total,
            needs_quote=it.needs_quote,
        )
        for it in i.items
    ]
    total = Decimal(str(snap["total"])) if snap.get("total") is not None else None
    return InquiryDetail(
        **b.model_dump(),
        contact_phone=i.contact_phone,
        contact_email=i.contact_email,
        work_place=i.work_place,
        comment=i.comment,
        items=items,
        extras=[ExtraOut(name=e.name_snapshot, price=e.price_snapshot) for e in i.extra_services],
        total_label=("от " if snap.get("is_partial") else "") + money(total),
        vat_label=snap.get("vat_label"),
        history=[
            HistoryOut(
                from_status=h.from_status,
                to_status=h.to_status,
                to_label=STATUS_LABELS[h.to_status],
                changed_by=str(h.changed_by) if h.changed_by else None,
                comment=h.comment,
                created_at=h.created_at,
            )
            for h in i.status_history
        ],
        comments=[
            CommentOut(
                id=c.id,
                author=str(c.author) if c.author else "Клиент",
                is_staff=bool(c.author and c.author.is_staff),
                is_internal=c.is_internal,
                text=c.text,
                created_at=c.created_at,
            )
            for c in i.comments
            if staff or not c.is_internal
        ],
        attachments=[
            AttachmentOut(
                public_id=a.public_id,
                original_name=a.original_name,
                content_type=a.content_type,
                size=a.size,
                kind=a.kind.value,
                uploaded_by=str(a.uploaded_by) if a.uploaded_by else None,
                created_at=a.created_at,
                download_url=f"/api/v1/files/{a.public_id}/download",
            )
            for a in i.attachments
        ],
        allowed_transitions=sorted(STATUS_TRANSITIONS[i.status], key=lambda s: s.value) if staff else [],
        parent_number=i.parent.number if i.parent else None,
    )


async def load_inquiry(session: AsyncSession, public_id, *, organization_id: int | None = None) -> Inquiry | None:
    stmt = (
        select(Inquiry)
        .options(*INQUIRY_LOAD)
        .execution_options(populate_existing=True)
        .where(Inquiry.public_id == public_id)
    )
    if organization_id is not None:
        stmt = stmt.where(Inquiry.organization_id == organization_id)
    return (await session.execute(stmt)).scalar_one_or_none()


def can_transition(user: User, from_status, to_status) -> bool:
    if user.role == Role.admin:
        return True
    return to_status in STATUS_TRANSITIONS[from_status]


__all__ = ["brief", "detail", "load_inquiry", "user_brief", "can_transition", "INQUIRY_LOAD", "BRIEF_LOAD", "Equipment"]
