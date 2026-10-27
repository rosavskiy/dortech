"""Создать/обновить администратора: uv run python -m scripts.create_admin email пароль [Фамилия Имя]"""

import asyncio
import sys
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models import Role, User


async def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("usage: create_admin email password [last_name first_name]")
    email, password = sys.argv[1].strip().lower(), sys.argv[2]
    last, first = (sys.argv[3] if len(sys.argv) > 3 else "Администратор"), (sys.argv[4] if len(sys.argv) > 4 else "")
    async with SessionLocal() as s:
        user = (await s.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if user is None:
            user = User(email=email, password_hash=hash_password(password), last_name=last, first_name=first)
            s.add(user)
        else:
            user.password_hash = hash_password(password)
        user.role = Role.admin
        user.is_active, user.blocked_at = True, None
        user.email_confirmed_at = user.email_confirmed_at or datetime.now(UTC)
        await s.commit()
    print(f"admin {email} ok")


if __name__ == "__main__":
    asyncio.run(main())
