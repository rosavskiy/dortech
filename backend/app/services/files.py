"""Приватные файлы заявок: проверка типа и размера, хранение вне веб-корня под UUID."""

import uuid
from pathlib import Path

import puremagic
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Attachment, AttachmentKind, Inquiry, User

MIME_BY_EXT = {
    "pdf": {"application/pdf"},
    "doc": {"application/msword", "application/x-ole-storage", "application/vnd.ms-office"},
    "docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/zip"},
    "xls": {"application/vnd.ms-excel", "application/x-ole-storage", "application/vnd.ms-office"},
    "xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/zip"},
    "jpg": {"image/jpeg"},
    "jpeg": {"image/jpeg"},
    "png": {"image/png"},
}
CHUNK = 1024 * 1024


async def save_attachment(
    session: AsyncSession,
    upload: UploadFile,
    *,
    inquiry: Inquiry,
    user: User,
    kind: AttachmentKind,
    allowed_ext: list[str] | None = None,
) -> Attachment:
    name = (upload.filename or "file").strip()
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    allowed = allowed_ext or settings.allowed_upload_extensions
    if ext not in allowed:
        raise HTTPException(400, f"Допустимые типы файлов: {', '.join(allowed)}")
    limit = settings.max_upload_mb * 1024 * 1024
    settings.private_root.mkdir(parents=True, exist_ok=True)
    dest: Path = settings.private_root / f"{uuid.uuid4().hex}.{ext}"
    size = 0
    head = b""
    with dest.open("wb") as out:
        while chunk := await upload.read(CHUNK):
            if not head:
                head = chunk[:4096]
            size += len(chunk)
            if size > limit:
                out.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(400, f"Файл больше {settings.max_upload_mb} МБ")
            out.write(chunk)
    if size == 0:
        dest.unlink(missing_ok=True)
        raise HTTPException(400, "Пустой файл")
    detected = _detect_mime(head, name)
    if detected is None or detected not in MIME_BY_EXT.get(ext, set()):
        dest.unlink(missing_ok=True)
        raise HTTPException(400, "Содержимое файла не соответствует его расширению")
    att = Attachment(
        inquiry_id=inquiry.id,
        organization_id=inquiry.organization_id,
        uploaded_by_id=user.id,
        path=dest.name,
        original_name=name[:255],
        content_type=detected,
        size=size,
        kind=kind,
    )
    session.add(att)
    await session.flush()
    return att


def _detect_mime(head: bytes, filename: str) -> str | None:
    try:
        matches = puremagic.magic_string(head)
    except Exception:
        return None
    if not matches:
        return None
    return matches[0].mime_type or None


def attachment_path(att: Attachment) -> Path:
    return settings.private_root / att.path


def can_access(att: Attachment, user: User) -> bool:
    if user.is_staff:
        return True
    return user.organization_id is not None and att.organization_id == user.organization_id
