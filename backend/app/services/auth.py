from datetime import UTC, datetime, timedelta

from fastapi import Request, Response
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password, new_token, token_hash
from app.models import EmailToken, EmailTokenKind, Organization, Role, User, UserSession
from app.services import outbox


class AuthError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


# ---------- сессии ----------


async def create_session(session: AsyncSession, user: User, request: Request) -> str:
    token = new_token(32)
    now = datetime.now(UTC)
    session.add(
        UserSession(
            token_hash=token_hash(token),
            user_id=user.id,
            created_at=now,
            expires_at=now + timedelta(days=settings.session_ttl_days),
            ip=request.client.host if request.client else None,
            user_agent=(request.headers.get("user-agent") or "")[:300],
        )
    )
    user.last_login_at = now
    return token


def set_auth_cookies(response: Response, token: str | None) -> str | None:
    secure = settings.is_production
    if token is None:
        response.delete_cookie(settings.session_cookie_name, path="/")
        response.delete_cookie(settings.csrf_cookie_name, path="/")
        return None
    csrf = new_token(24)
    max_age = settings.session_ttl_days * 86400
    response.set_cookie(
        settings.session_cookie_name, token, max_age=max_age, httponly=True, secure=secure, samesite="lax", path="/"
    )
    response.set_cookie(
        settings.csrf_cookie_name, csrf, max_age=max_age, httponly=False, secure=secure, samesite="lax", path="/"
    )
    return csrf


async def delete_session(session: AsyncSession, token: str | None) -> None:
    if token:
        await session.execute(delete(UserSession).where(UserSession.token_hash == token_hash(token)))


async def delete_all_sessions(session: AsyncSession, user_id: int) -> None:
    await session.execute(delete(UserSession).where(UserSession.user_id == user_id))


# ---------- email-токены ----------


async def issue_email_token(session: AsyncSession, user: User, kind: EmailTokenKind) -> str:
    token = new_token(32)
    session.add(
        EmailToken(
            user_id=user.id,
            kind=kind,
            token_hash=token_hash(token),
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=settings.email_token_ttl_hours),
        )
    )
    return token


async def consume_email_token(session: AsyncSession, token: str, kind: EmailTokenKind) -> User:
    row = (
        await session.execute(
            select(EmailToken).where(EmailToken.token_hash == token_hash(token), EmailToken.kind == kind)
        )
    ).scalar_one_or_none()
    if row is None or row.used_at is not None or row.expires_at < datetime.now(UTC):
        raise AuthError("Ссылка недействительна или устарела", 400)
    row.used_at = datetime.now(UTC)
    user = await session.get(User, row.user_id)
    if user is None:
        raise AuthError("Пользователь не найден", 400)
    return user


# ---------- регистрация и восстановление ----------


def validate_password(password: str) -> None:
    if len(password) < 8:
        raise AuthError("Пароль должен содержать не менее 8 символов")
    if password.isdigit() or password.isalpha():
        raise AuthError("Пароль должен содержать и буквы, и цифры")


async def register(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    phone: str | None,
    company_name: str,
    inn: str | None,
) -> User:
    email = email.strip().lower()
    validate_password(password)
    exists = (await session.execute(select(User.id).where(User.email == email))).scalar_one_or_none()
    if exists:
        raise AuthError("Пользователь с таким email уже зарегистрирован", 409)
    org = Organization(name=company_name.strip(), inn=(inn or "").strip() or None)
    session.add(org)
    await session.flush()
    user = User(
        email=email,
        password_hash=hash_password(password),
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        phone=phone,
        role=Role.client,
        organization_id=org.id,
    )
    session.add(user)
    await session.flush()
    await send_confirmation(session, user)
    return user


async def send_confirmation(session: AsyncSession, user: User) -> None:
    token = await issue_email_token(session, user, EmailTokenKind.confirm)
    outbox.enqueue_email(
        session,
        user.email,
        "Подтверждение регистрации — Дортех",
        "confirm_email",
        {"name": user.first_name or user.email, "link": f"{settings.site_url}/register/confirm?token={token}"},
    )


async def request_password_reset(session: AsyncSession, email: str) -> None:
    user = (await session.execute(select(User).where(User.email == email.strip().lower()))).scalar_one_or_none()
    if user is None or not user.can_login:
        return
    token = await issue_email_token(session, user, EmailTokenKind.reset)
    outbox.enqueue_email(
        session,
        user.email,
        "Восстановление пароля — Дортех",
        "password_reset",
        {"name": user.first_name or user.email, "link": f"{settings.site_url}/password-reset/confirm?token={token}"},
    )


async def reset_password(session: AsyncSession, token: str, password: str) -> User:
    validate_password(password)
    user = await consume_email_token(session, token, EmailTokenKind.reset)
    user.password_hash = hash_password(password)
    if user.email_confirmed_at is None:
        user.email_confirmed_at = datetime.now(UTC)
    await delete_all_sessions(session, user.id)
    return user
