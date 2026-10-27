from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.deps import client_ip, csrf_protect, current_organization, require_client
from app.core.pagination import Paginated, to_int
from app.models import AttachmentKind, Inquiry, InquiryComment, InquirySource, InquiryStatus, Organization, User
from app.schemas.account import CommentIn, InquiryBrief, InquiryDetail, ProfileIn
from app.schemas.auth import MeOut
from app.schemas.inquiries import InquiryCreatedOut, InquiryCreateIn
from app.services import files as files_svc
from app.services import inquiry_views as views
from app.services.audit import log_action
from app.services.inquiries import create_inquiry

router = APIRouter(prefix="/account", tags=["account"], dependencies=[Depends(csrf_protect)])


@router.get("/profile", response_model=MeOut)
async def profile(user: User = Depends(require_client)):
    from app.api.auth import me_out

    return me_out(user)


@router.patch("/profile", response_model=MeOut)
async def update_profile(
    data: ProfileIn,
    request: Request,
    user: User = Depends(require_client),
    org: Organization = Depends(current_organization),
    session: AsyncSession = Depends(get_session),
):
    from app.api.auth import me_out

    user = await session.merge(user)
    org = await session.merge(org)
    user.first_name, user.last_name, user.patronymic = data.first_name, data.last_name, data.patronymic
    user.phone, user.position = data.phone, data.position
    org.name, org.inn, org.kpp = data.org_name, data.org_inn or None, data.org_kpp or None
    org.legal_address, org.phone, org.email = data.org_legal_address, data.org_phone, data.org_email
    log_action(session, actor=user, action="profile.update", target=org, ip=client_ip(request))
    await session.commit()
    await session.refresh(user, ["organization"])
    return me_out(user)


@router.get("/inquiries", response_model=Paginated[InquiryBrief])
async def my_inquiries(
    status: str | None = None,
    page: str | None = None,
    org: Organization = Depends(current_organization),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Inquiry).where(Inquiry.organization_id == org.id)
    if status and status in InquiryStatus.__members__:
        stmt = stmt.where(Inquiry.status == InquiryStatus(status))
    total = (await session.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    size, page_n = 20, to_int(page, 1)
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


@router.post("/inquiries", response_model=InquiryCreatedOut, status_code=201)
async def create_from_account(
    data: InquiryCreateIn,
    request: Request,
    user: User = Depends(require_client),
    org: Organization = Depends(current_organization),
    session: AsyncSession = Depends(get_session),
):
    user = await session.merge(user)
    try:
        inquiry, est = await create_inquiry(
            session, data, user=user, ip=client_ip(request), source=InquirySource.account
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    await session.commit()
    await session.refresh(inquiry)
    return InquiryCreatedOut(
        public_id=inquiry.public_id,
        number=inquiry.number,
        status=inquiry.status,
        estimate=est,
        created_at=inquiry.created_at,
    )


@router.get("/inquiries/{public_id}", response_model=InquiryDetail)
async def my_inquiry(
    public_id: UUID,
    user: User = Depends(require_client),
    org: Organization = Depends(current_organization),
    session: AsyncSession = Depends(get_session),
):
    i = await views.load_inquiry(session, public_id, organization_id=org.id)
    if i is None:
        raise HTTPException(404, "Заявка не найдена")
    return views.detail(i, viewer=user)


@router.post("/inquiries/{public_id}/comments", response_model=InquiryDetail, status_code=201)
async def add_comment(
    public_id: UUID,
    data: CommentIn,
    user: User = Depends(require_client),
    org: Organization = Depends(current_organization),
    session: AsyncSession = Depends(get_session),
):
    i = await views.load_inquiry(session, public_id, organization_id=org.id)
    if i is None:
        raise HTTPException(404, "Заявка не найдена")
    session.add(InquiryComment(inquiry_id=i.id, author_id=user.id, text=data.text.strip(), is_internal=False))
    await session.commit()
    i = await views.load_inquiry(session, public_id, organization_id=org.id)
    return views.detail(i, viewer=user)


@router.post("/inquiries/{public_id}/files", response_model=InquiryDetail, status_code=201)
async def upload_file(
    public_id: UUID,
    file: UploadFile,
    request: Request,
    user: User = Depends(require_client),
    org: Organization = Depends(current_organization),
    session: AsyncSession = Depends(get_session),
):
    i = await views.load_inquiry(session, public_id, organization_id=org.id)
    if i is None:
        raise HTTPException(404, "Заявка не найдена")
    user = await session.merge(user)
    att = await files_svc.save_attachment(session, file, inquiry=i, user=user, kind=AttachmentKind.client_doc)
    log_action(session, actor=user, action="file.upload", target=att, ip=client_ip(request))
    await session.commit()
    i = await views.load_inquiry(session, public_id, organization_id=org.id)
    return views.detail(i, viewer=user)
