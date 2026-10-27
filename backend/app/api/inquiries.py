from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.limiter import limiter
from app.models import ContactMessage, ExtraService
from app.schemas.inquiries import ContactMessageIn, EstimateIn, EstimateOut, InquiryCreatedOut, InquiryCreateIn
from app.services import outbox
from app.services.inquiries import create_inquiry
from app.services.pricing import estimate

router = APIRouter(tags=["inquiries"])


@router.get("/inquiries/extra-services")
async def extra_services(session: AsyncSession = Depends(get_session)) -> list[dict]:
    rows = (
        (
            await session.execute(
                select(ExtraService).where(ExtraService.is_active.is_(True)).order_by(ExtraService.sort)
            )
        )
        .scalars()
        .all()
    )
    return [{"id": s.id, "name": s.name, "description": s.description, "price": s.price} for s in rows]


@router.post("/inquiries/estimate", response_model=EstimateOut)
@limiter.limit("60/minute")
async def estimate_endpoint(request: Request, data: EstimateIn, session: AsyncSession = Depends(get_session)):
    return await estimate(session, data)


@router.post("/inquiries", response_model=InquiryCreatedOut, status_code=201)
@limiter.limit("10/hour")
async def create(request: Request, data: InquiryCreateIn, session: AsyncSession = Depends(get_session)):
    if data.website:  # honeypot
        raise HTTPException(400, "Некорректная заявка")
    try:
        inquiry, est = await create_inquiry(
            session, data, user=None, ip=request.client.host if request.client else None
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


@router.post("/contact-messages", status_code=201)
@limiter.limit("10/hour")
async def contact_message(
    request: Request, data: ContactMessageIn, session: AsyncSession = Depends(get_session)
) -> dict:
    if data.website:
        raise HTTPException(400, "Некорректное сообщение")
    msg = ContactMessage(
        name=data.name.strip(),
        phone=data.phone,
        email=data.email,
        text=data.text.strip(),
        ip=request.client.host if request.client else None,
    )
    session.add(msg)
    await session.flush()
    from app.core.config import settings

    if settings.notification_emails:
        outbox.enqueue_email(
            session,
            settings.notification_emails,
            "Новое сообщение с сайта",
            "contact_message",
            {"name": msg.name, "phone": msg.phone, "email": msg.email, "text": msg.text},
        )
    await session.commit()
    return {"ok": True, "id": msg.id}
