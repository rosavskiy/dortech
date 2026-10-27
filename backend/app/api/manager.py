import csv
import io
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.deps import client_ip, csrf_protect, require_staff
from app.core.pagination import Paginated, to_int
from app.models import STATUS_LABELS, AttachmentKind, Inquiry, InquiryComment, InquiryStatus, Organization, Role, User
from app.schemas.account import AssignIn, CommentIn, InquiryBrief, InquiryDetail, StatusIn, UserBrief
from app.schemas.auth import OrganizationOut
from app.services import files as files_svc
from app.services import inquiry_views as views
from app.services import outbox
from app.services.audit import log_action
from app.services.inquiries import change_status, inquiry_payload

router = APIRouter(prefix="/manager", tags=["manager"], dependencies=[Depends(csrf_protect)])


def _filters(
    stmt,
    *,
    status: str | None,
    assigned_to: str | None,
    organization: str | None,
    date_from: str | None,
    date_to: str | None,
    q: str | None,
):
    if status and status in InquiryStatus.__members__:
        stmt = stmt.where(Inquiry.status == InquiryStatus(status))
    if assigned_to:
        if assigned_to == "none":
            stmt = stmt.where(Inquiry.assigned_to_id.is_(None))
        elif assigned_to.isdigit():
            stmt = stmt.where(Inquiry.assigned_to_id == int(assigned_to))
    if organization and organization.isdigit():
        stmt = stmt.where(Inquiry.organization_id == int(organization))
    for value, op in ((date_from, ">="), (date_to, "<=")):
        try:
            d = date.fromisoformat(value) if value else None
        except ValueError:
            d = None
        if d:
            stmt = (
                stmt.where(func.date(Inquiry.created_at) >= d)
                if op == ">="
                else stmt.where(func.date(Inquiry.created_at) <= d)
            )
    if q and (q := q.strip()[:100]):
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Inquiry.number.ilike(like),
                Inquiry.contact_name.ilike(like),
                Inquiry.contact_phone.ilike(like),
                Inquiry.contact_email.ilike(like),
                Inquiry.company_name_raw.ilike(like),
            )
        )
    return stmt


@router.get("/inquiries", response_model=Paginated[InquiryBrief])
async def inquiries(
    status: str | None = None,
    assigned_to: str | None = None,
    organization: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    q: str | None = None,
    page: str | None = None,
    user: User = Depends(require_staff),
    session: AsyncSession = Depends(get_session),
):
    stmt = _filters(
        select(Inquiry),
        status=status,
        assigned_to=assigned_to,
        organization=organization,
        date_from=date_from,
        date_to=date_to,
        q=q,
    )
    total = (await session.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    size, page_n = 25, to_int(page, 1)
    pages = max((total + size - 1) // size, 1)
    page_n = min(page_n, pages)
    rows = (
        (
            await session.execute(
                stmt.options(*views.BRIEF_LOAD)
                .order_by(Inquiry.created_at.desc())
                .offset((page_n - 1) * size)
                .limit(size)
            )
        )
        .scalars()
        .unique()
        .all()
    )
    return Paginated(items=[views.brief(i) for i in rows], page=page_n, page_size=size, total=total, pages=pages)


@router.get("/inquiries/export.csv")
async def export_csv(
    status: str | None = None,
    assigned_to: str | None = None,
    organization: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    q: str | None = None,
    user: User = Depends(require_staff),
    session: AsyncSession = Depends(get_session),
):
    stmt = _filters(
        select(Inquiry),
        status=status,
        assigned_to=assigned_to,
        organization=organization,
        date_from=date_from,
        date_to=date_to,
        q=q,
    )
    rows = (
        (await session.execute(stmt.options(*views.INQUIRY_LOAD).order_by(Inquiry.created_at.desc()).limit(5000)))
        .scalars()
        .unique()
        .all()
    )
    buf = io.StringIO()
    buf.write("﻿")
    w = csv.writer(buf, delimiter=";")
    w.writerow(
        [
            "Номер",
            "Дата",
            "Статус",
            "Организация",
            "Контакт",
            "Телефон",
            "Email",
            "Период с",
            "Период по",
            "Место",
            "Позиции",
            "Сумма",
            "Ответственный",
            "Источник",
        ]
    )
    for i in rows:
        b = views.brief(i)
        w.writerow(
            [
                b.number,
                i.created_at.strftime("%d.%m.%Y %H:%M"),
                b.status_label,
                b.organization or "",
                i.contact_name,
                i.contact_phone,
                i.contact_email or "",
                i.period_from.isoformat() if i.period_from else "",
                i.period_to.isoformat() if i.period_to else "",
                (i.work_place or "").replace("\n", " "),
                "; ".join(f"{it.name_snapshot} × {it.quantity} ({it.units} {it.unit.value})" for it in i.items),
                f"{b.estimated_total:.2f}".replace(".", ",") if b.estimated_total is not None else "",
                b.assigned_to.name if b.assigned_to else "",
                b.source,
            ]
        )
    buf.seek(0)
    fname = f"inquiries-{date.today().isoformat()}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@router.get("/inquiries/{public_id}", response_model=InquiryDetail)
async def inquiry(public_id: UUID, user: User = Depends(require_staff), session: AsyncSession = Depends(get_session)):
    i = await views.load_inquiry(session, public_id)
    if i is None:
        raise HTTPException(404, "Заявка не найдена")
    return views.detail(i, viewer=user)


@router.patch("/inquiries/{public_id}", response_model=InquiryDetail)
async def assign(
    public_id: UUID,
    data: AssignIn,
    request: Request,
    user: User = Depends(require_staff),
    session: AsyncSession = Depends(get_session),
):
    i = await views.load_inquiry(session, public_id)
    if i is None:
        raise HTTPException(404, "Заявка не найдена")
    if data.assigned_to_id is not None:
        target = await session.get(User, data.assigned_to_id)
        if target is None or not target.is_staff:
            raise HTTPException(400, "Ответственным может быть только сотрудник")
    old = i.assigned_to_id
    i.assigned_to_id = data.assigned_to_id
    log_action(
        session,
        actor=user,
        action="inquiry.assign",
        target=i,
        changes={"from": old, "to": data.assigned_to_id},
        ip=client_ip(request),
    )
    await session.commit()
    return views.detail(await views.load_inquiry(session, public_id), viewer=user)


@router.post("/inquiries/{public_id}/status", response_model=InquiryDetail)
async def set_status(
    public_id: UUID,
    data: StatusIn,
    request: Request,
    user: User = Depends(require_staff),
    session: AsyncSession = Depends(get_session),
):
    i = await views.load_inquiry(session, public_id)
    if i is None:
        raise HTTPException(404, "Заявка не найдена")
    if data.status == i.status:
        raise HTTPException(400, "Заявка уже в этом статусе")
    if not views.can_transition(user, i.status, data.status):
        raise HTTPException(400, f"Переход «{STATUS_LABELS[i.status]}» → «{STATUS_LABELS[data.status]}» недопустим")
    old = i.status
    change_status(session, i, data.status, actor=user, comment=data.comment)
    log_action(
        session,
        actor=user,
        action="inquiry.status",
        target=i,
        changes={"from": old.value, "to": data.status.value},
        ip=client_ip(request),
    )
    if i.contact_email:
        outbox.enqueue_email(
            session,
            i.contact_email,
            f"Заявка {i.number}: {STATUS_LABELS[data.status]}",
            "inquiry_status_changed",
            {**inquiry_payload(i), "comment_for_client": data.comment},
        )
    await session.commit()
    return views.detail(await views.load_inquiry(session, public_id), viewer=user)


@router.post("/inquiries/{public_id}/comments", response_model=InquiryDetail, status_code=201)
async def comment(
    public_id: UUID, data: CommentIn, user: User = Depends(require_staff), session: AsyncSession = Depends(get_session)
):
    i = await views.load_inquiry(session, public_id)
    if i is None:
        raise HTTPException(404, "Заявка не найдена")
    session.add(
        InquiryComment(inquiry_id=i.id, author_id=user.id, text=data.text.strip(), is_internal=data.is_internal)
    )
    await session.commit()
    return views.detail(await views.load_inquiry(session, public_id), viewer=user)


@router.post("/inquiries/{public_id}/files", response_model=InquiryDetail, status_code=201)
async def upload_offer(
    public_id: UUID,
    file: UploadFile,
    request: Request,
    user: User = Depends(require_staff),
    session: AsyncSession = Depends(get_session),
):
    i = await views.load_inquiry(session, public_id)
    if i is None:
        raise HTTPException(404, "Заявка не найдена")
    user = await session.merge(user)
    att = await files_svc.save_attachment(
        session, file, inquiry=i, user=user, kind=AttachmentKind.offer_pdf, allowed_ext=["pdf"]
    )
    log_action(session, actor=user, action="file.offer_upload", target=att, ip=client_ip(request))
    await session.commit()
    return views.detail(await views.load_inquiry(session, public_id), viewer=user)


@router.get("/organizations", response_model=list[OrganizationOut])
async def organizations(
    q: str | None = None, user: User = Depends(require_staff), session: AsyncSession = Depends(get_session)
):
    stmt = select(Organization).order_by(Organization.name)
    if q:
        like = f"%{q.strip()[:100]}%"
        stmt = stmt.where(or_(Organization.name.ilike(like), Organization.inn.ilike(like)))
    rows = (await session.execute(stmt.limit(200))).scalars().all()
    return [
        OrganizationOut(
            id=o.id, name=o.name, inn=o.inn, kpp=o.kpp, legal_address=o.legal_address, phone=o.phone, email=o.email
        )
        for o in rows
    ]


@router.get("/managers", response_model=list[UserBrief])
async def managers(user: User = Depends(require_staff), session: AsyncSession = Depends(get_session)):
    rows = (
        (
            await session.execute(
                select(User)
                .where(User.role.in_([Role.manager, Role.admin]), User.is_active.is_(True), User.blocked_at.is_(None))
                .order_by(User.last_name)
            )
        )
        .scalars()
        .all()
    )
    return [views.user_brief(u) for u in rows]


@router.get("/statuses")
async def statuses(user: User = Depends(require_staff)) -> list[dict]:
    return [{"value": k.value, "label": v} for k, v in STATUS_LABELS.items()]
