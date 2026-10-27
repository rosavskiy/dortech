from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_session

router = APIRouter()


@router.get("/health")
async def health(session: AsyncSession = Depends(get_session)) -> dict:
    db_ok = True
    try:
        await session.execute(text("select 1"))
    except Exception:
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "version": settings.app_version,
        "commit": settings.git_commit,
        "environment": settings.environment,
        "database": "ok" if db_ok else "error",
    }
