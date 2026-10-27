from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.db import get_session
from app.core.deps import csrf_protect, get_current_user, require_user
from app.core.limiter import limiter
from app.core.security import new_token, verify_password
from app.models import EmailTokenKind, User
from app.schemas.auth import EmailIn, LoginIn, MeOut, OrganizationOut, RegisterIn, ResetConfirmIn, TokenIn
from app.services import auth as svc

router = APIRouter(prefix="/auth", tags=["auth"])


def me_out(user: User, csrf: str | None = None) -> MeOut:
    org = user.organization
    return MeOut(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        patronymic=user.patronymic,
        phone=user.phone,
        position=user.position,
        role=user.role.value,
        organization=OrganizationOut(
            id=org.id,
            name=org.name,
            inn=org.inn,
            kpp=org.kpp,
            legal_address=org.legal_address,
            phone=org.phone,
            email=org.email,
        )
        if org
        else None,
        csrf_token=csrf,
    )


async def _login_response(session: AsyncSession, user: User, request: Request, response: Response) -> MeOut:
    token = await svc.create_session(session, user, request)
    await session.commit()
    csrf = svc.set_auth_cookies(response, token)
    await session.refresh(user, ["organization"])
    return me_out(user, csrf)


@router.get("/me", response_model=MeOut)
async def me(request: Request, response: Response, user: User = Depends(require_user)):
    csrf = request.cookies.get(settings.csrf_cookie_name)
    if not csrf:
        csrf = new_token(24)
        response.set_cookie(
            settings.csrf_cookie_name,
            csrf,
            max_age=settings.session_ttl_days * 86400,
            httponly=False,
            secure=settings.is_production,
            samesite="lax",
            path="/",
        )
    return me_out(user, csrf)


@router.post("/register", status_code=201)
@limiter.limit("5/minute")
async def register(request: Request, data: RegisterIn, session: AsyncSession = Depends(get_session)) -> dict:
    if data.website:
        raise HTTPException(400, "Некорректный запрос")
    try:
        await svc.register(
            session,
            email=data.email,
            password=data.password,
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            company_name=data.company_name,
            inn=data.inn,
        )
    except svc.AuthError as e:
        raise HTTPException(e.status, str(e)) from e
    await session.commit()
    return {"ok": True, "message": "Мы отправили письмо для подтверждения email"}


@router.post("/resend-confirmation")
@limiter.limit("3/minute")
async def resend(request: Request, data: EmailIn, session: AsyncSession = Depends(get_session)) -> dict:
    user = (await session.execute(select(User).where(User.email == data.email.lower()))).scalar_one_or_none()
    if user and user.email_confirmed_at is None and user.can_login:
        await svc.send_confirmation(session, user)
        await session.commit()
    return {"ok": True}


@router.post("/confirm-email", response_model=MeOut)
async def confirm_email(
    request: Request, response: Response, data: TokenIn, session: AsyncSession = Depends(get_session)
):
    from datetime import UTC, datetime

    try:
        user = await svc.consume_email_token(session, data.token, EmailTokenKind.confirm)
    except svc.AuthError as e:
        raise HTTPException(e.status, str(e)) from e
    if user.email_confirmed_at is None:
        user.email_confirmed_at = datetime.now(UTC)
    if not user.can_login:
        raise HTTPException(403, "Учётная запись заблокирована")
    return await _login_response(session, user, request, response)


@router.post("/login", response_model=MeOut)
@limiter.limit("10/minute")
async def login(request: Request, response: Response, data: LoginIn, session: AsyncSession = Depends(get_session)):
    user = (
        await session.execute(
            select(User).options(selectinload(User.organization)).where(User.email == data.email.lower())
        )
    ).scalar_one_or_none()
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(400, "Неверный email или пароль")
    if not user.can_login:
        raise HTTPException(403, "Учётная запись заблокирована")
    if user.email_confirmed_at is None:
        raise HTTPException(403, "Подтвердите email по ссылке из письма")
    return await _login_response(session, user, request, response)


@router.post("/logout", dependencies=[Depends(csrf_protect)])
async def logout(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
    user: User | None = Depends(get_current_user),
) -> dict:
    await svc.delete_session(session, request.cookies.get(settings.session_cookie_name))
    await session.commit()
    svc.set_auth_cookies(response, None)
    return {"ok": True}


@router.post("/password-reset")
@limiter.limit("3/minute")
async def password_reset(request: Request, data: EmailIn, session: AsyncSession = Depends(get_session)) -> dict:
    await svc.request_password_reset(session, data.email)
    await session.commit()
    return {"ok": True, "message": "Если адрес зарегистрирован, мы отправили письмо со ссылкой"}


@router.post("/password-reset/confirm", response_model=MeOut)
async def password_reset_confirm(
    request: Request, response: Response, data: ResetConfirmIn, session: AsyncSession = Depends(get_session)
):
    try:
        user = await svc.reset_password(session, data.token, data.password)
    except svc.AuthError as e:
        raise HTTPException(e.status, str(e)) from e
    if not user.can_login:
        raise HTTPException(403, "Учётная запись заблокирована")
    return await _login_response(session, user, request, response)
