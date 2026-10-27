from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.deps import require_user
from app.models import Attachment, User
from app.services import files as files_svc

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/{public_id}/download")
async def download(public_id: UUID, user: User = Depends(require_user), session: AsyncSession = Depends(get_session)):
    att = (await session.execute(select(Attachment).where(Attachment.public_id == public_id))).scalar_one_or_none()
    # чужой файл неотличим от несуществующего (ТЗ 6, «Разделение доступа»)
    if att is None or not files_svc.can_access(att, user):
        raise HTTPException(404, "Файл не найден")
    path = files_svc.attachment_path(att)
    if not path.exists():
        raise HTTPException(404, "Файл не найден")
    return FileResponse(
        path, media_type=att.content_type, filename=att.original_name, headers={"Cache-Control": "private, no-store"}
    )
