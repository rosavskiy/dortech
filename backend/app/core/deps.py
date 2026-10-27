"""Зависимости FastAPI: текущий пользователь, роли, организация, CSRF."""

from collections.abc import Callable
from datetime import UTC, datetime

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.db import get_session
from app.core.security import token_hash
from app.models import Organization, Role, User, UserSession

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


async def get_current_user(request: Request, session: AsyncSession = Depends(get_session)) -> User | None:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None
    row = (
        await session.execute(
            select(UserSession)
            .options(selectinload(UserSession.user).selectinload(User.organization))
            .where(UserSession.token_hash == token_hash(token))
        )
    ).scalar_one_or_none()
    if row is None or row.expires_at < datetime.now(UTC):
        return None
    user = row.user
    if not user.can_login:
        return None
    request.state.user = user
    request.state.user_session = row
    return user


async def require_user(user: User | None = Depends(get_current_user)) -> User:
    if user is None:
        raise HTTPException(401, "Требуется вход")
    return user


def require_role(*roles: Role) -> Callable:
    async def _dep(user: User = Depends(require_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, "Недостаточно прав")
        return user

    return _dep


require_client = require_role(Role.client)
require_staff = require_role(Role.manager, Role.admin)
require_admin = require_role(Role.admin)


async def current_organization(user: User = Depends(require_client)) -> Organization:
    if user.organization is None:
        raise HTTPException(403, "Профиль организации не заполнен")
    return user.organization


async def csrf_protect(request: Request) -> None:
    """Double-submit cookie: для небезопасных методов заголовок должен совпадать с cookie."""
    if request.method in SAFE_METHODS:
        return
    cookie = request.cookies.get(settings.csrf_cookie_name)
    header = request.headers.get("X-CSRF-Token")
    if not cookie or not header or cookie != header:
        raise HTTPException(403, "Недействительный CSRF-токен")


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None
