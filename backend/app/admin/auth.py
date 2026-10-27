from datetime import UTC, datetime

from sqlalchemy import select
from starlette.requests import Request
from starlette_admin.auth import AdminUser, AuthProvider, LoginFailed

from app.core.db import SessionLocal
from app.core.security import verify_password
from app.models import Role, User


class StaffAuthProvider(AuthProvider):
    """Вход в панель по email/паролю. Доступ — только роли manager и admin, не заблокированные."""

    async def login(self, username: str, password: str, remember_me: bool, request: Request):
        async with SessionLocal() as session:
            user = (
                await session.execute(select(User).where(User.email == username.strip().lower()))
            ).scalar_one_or_none()
            if user is None or not verify_password(password, user.password_hash):
                raise LoginFailed("Неверный email или пароль")
            if not user.can_login or not user.is_staff:
                raise LoginFailed("Доступ в панель запрещён")
            user.last_login_at = datetime.now(UTC)
            await session.commit()
            request.session.update({"admin_user_id": user.id, "admin_role": user.role.value})

    async def authenticate(self, request: Request) -> AdminUser | None:
        user_id = request.session.get("admin_user_id")
        if not user_id:
            return None
        async with SessionLocal() as session:
            user = await session.get(User, user_id)
            if user is None or not user.can_login or not user.is_staff:
                request.session.clear()
                return None
            request.session["admin_role"] = user.role.value
            request.state.current_user = user
            return AdminUser(username=str(user))

    async def logout(self, request: Request):
        request.session.clear()


def role_of(request: Request) -> Role | None:
    value = request.session.get("admin_role")
    return Role(value) if value else None
