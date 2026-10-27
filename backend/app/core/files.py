"""Публичные файлы (картинки каталога и контента) хранит starlette-admin в JSON-описании."""

from app.core.config import settings


def file_url(file: dict | None) -> str | None:
    if not file or not isinstance(file, dict):
        return None
    key = file.get("key")
    if not key:
        return None
    return f"/media/public/{key.lstrip('/')}"


def file_record(key: str, filename: str, content_type: str, size: int, storage: str = "media") -> dict:
    return {
        "filename": filename,
        "content_type": content_type,
        "size": size,
        "storage": storage,
        "key": key,
        "url": "",
    }


__all__ = ["file_url", "file_record", "settings"]
