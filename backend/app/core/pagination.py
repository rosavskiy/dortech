from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

DEFAULT_PAGE_SIZE = 24
MAX_PAGE_SIZE = 60


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int
    pages: int


def to_int(value: str | None, default: int, minimum: int = 1, maximum: int | None = None) -> int:
    """Терпимый разбор чисел из query: мусор → значение по умолчанию (ТЗ 2.3)."""
    try:
        n = int(str(value).strip())
    except (TypeError, ValueError):
        return default
    if n < minimum:
        return minimum
    if maximum is not None and n > maximum:
        return maximum
    return n
