"""Импорт каталога из CSV (ТЗ 5.1): валидация строк, отчёт об ошибках, upsert по external_id.

Формат: UTF-8 (с BOM или без), разделитель «;». Колонки — см. docs/CSV_TEMPLATE.md.
"""

import csv
import io
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.files import file_record
from app.core.slug import slugify
from app.models import (
    AttributeDefinition,
    AttributeOption,
    AttributeType,
    AttributeValue,
    AvailabilityStatus,
    Category,
    Equipment,
    EquipmentImage,
    ImportJob,
    ImportStatus,
    Manufacturer,
    Tariff,
)

REQUIRED = ["external_id", "name", "category"]
KNOWN = {
    "external_id",
    "name",
    "slug",
    "category",
    "manufacturer",
    "model",
    "year",
    "status",
    "short_description",
    "description",
    "terms",
    "price_per_shift",
    "price_per_day",
    "shift_hours",
    "min_units",
    "price_hidden",
    "is_published",
    "is_featured",
    "sort",
    "images",
    "meta_title",
    "meta_description",
}
TRUE = {"1", "true", "yes", "да", "y", "д"}
FALSE = {"0", "false", "no", "нет", "n", "н", ""}


@dataclass
class Issue:
    row: int
    external_id: str
    field: str
    message: str
    level: str = "error"  # error | warning

    def as_dict(self) -> dict:
        return {
            "row": self.row,
            "external_id": self.external_id,
            "field": self.field,
            "message": self.message,
            "level": self.level,
        }


@dataclass
class Result:
    total: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    issues: list[Issue] = field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "error"]


class HeaderError(Exception):
    pass


def _dec(v: str) -> Decimal | None:
    v = (v or "").strip().replace(" ", "").replace(",", ".")
    if not v:
        return None
    try:
        return Decimal(v)
    except InvalidOperation as e:
        raise ValueError("ожидалось число") from e


def _int(v: str) -> int | None:
    v = (v or "").strip()
    if not v:
        return None
    if not re.fullmatch(r"-?\d+", v):
        raise ValueError("ожидалось целое число")
    return int(v)


def _bool(v: str) -> bool | None:
    s = (v or "").strip().lower()
    if s in TRUE:
        return True
    if s in FALSE:
        return None if s == "" else False
    raise ValueError("ожидалось да/нет (1/0)")


def parse_csv(data: bytes) -> tuple[list[str], list[dict[str, str]]]:
    text = data.decode("utf-8-sig")
    sample = text[:2048]
    delimiter = ";" if sample.count(";") >= sample.count(",") else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    headers = [h.strip() for h in (reader.fieldnames or [])]
    missing = [h for h in REQUIRED if h not in headers]
    if missing:
        raise HeaderError("Нет обязательных колонок: " + ", ".join(missing))
    rows = []
    for raw in reader:
        rows.append({(k or "").strip(): (v or "").strip() for k, v in raw.items() if k is not None})
    return headers, rows


async def import_catalog(session: AsyncSession, data: bytes, *, dry_run: bool, job: ImportJob | None = None) -> Result:
    res = Result()
    headers, rows = parse_csv(data)
    res.total = len(rows)
    attr_codes = {h[5:] for h in headers if h.startswith("attr:")}
    unknown = [h for h in headers if h not in KNOWN and not h.startswith("attr:")]
    for h in unknown:
        res.issues.append(Issue(0, "", h, "Неизвестная колонка проигнорирована", "warning"))

    # справочники
    cats = {c.slug: c for c in (await session.execute(select(Category))).scalars()}
    mans = {m.name.lower(): m for m in (await session.execute(select(Manufacturer))).scalars()}
    statuses = {s.code: s for s in (await session.execute(select(AvailabilityStatus))).scalars()}
    attrs = {
        a.code: a
        for a in (
            await session.execute(select(AttributeDefinition).options(selectinload(AttributeDefinition.options)))
        ).scalars()
    }
    for code in attr_codes:
        if code not in attrs:
            res.issues.append(
                Issue(0, "", f"attr:{code}", "Характеристика не найдена в словаре, колонка проигнорирована", "warning")
            )
    existing = {
        e.external_id: e
        for e in (
            await session.execute(
                select(Equipment)
                .options(
                    selectinload(Equipment.tariff),
                    selectinload(Equipment.attribute_values),
                    selectinload(Equipment.images),
                )
                .where(Equipment.external_id.isnot(None))
            )
        ).scalars()
    }
    used_slugs = set((await session.execute(select(Equipment.slug))).scalars())

    # дубли внутри файла: последняя строка побеждает
    last_row_for: dict[str, int] = {}
    for n, row in enumerate(rows, start=2):
        ext = row.get("external_id", "")
        if ext in last_row_for:
            res.issues.append(
                Issue(last_row_for[ext], ext, "external_id", f"Дубль в файле, использована строка {n}", "warning")
            )
            res.skipped += 1
        last_row_for[ext] = n

    import_dir = settings.media_root / "public" / "import"
    for n, row in enumerate(rows, start=2):
        ext = row.get("external_id", "")
        if not ext:
            res.issues.append(Issue(n, "", "external_id", "Пустой внешний идентификатор"))
            res.failed += 1
            continue
        if last_row_for[ext] != n:
            continue
        errors: list[Issue] = []
        values: dict = {}
        name = row.get("name", "")
        if not name:
            errors.append(Issue(n, ext, "name", "Пустое название"))
        cat = cats.get(row.get("category", ""))
        if cat is None:
            errors.append(Issue(n, ext, "category", f"Категория «{row.get('category', '')}» не найдена (нужен slug)"))
        status = None
        if row.get("status"):
            status = statuses.get(row["status"])
            if status is None:
                errors.append(Issue(n, ext, "status", f"Статус «{row['status']}» не найден (нужен код)"))
        for key, fn in (
            ("year", _int),
            ("shift_hours", _int),
            ("min_units", _int),
            ("sort", _int),
            ("price_per_shift", _dec),
            ("price_per_day", _dec),
            ("price_hidden", _bool),
            ("is_published", _bool),
            ("is_featured", _bool),
        ):
            if key in row:
                try:
                    values[key] = fn(row[key])
                except ValueError as e:
                    errors.append(Issue(n, ext, key, str(e)))
        attr_vals: list[tuple[AttributeDefinition, dict]] = []
        for code in attr_codes:
            a = attrs.get(code)
            raw = row.get(f"attr:{code}", "")
            if a is None or raw == "":
                continue
            try:
                if a.type == AttributeType.number:
                    d = _dec(raw)
                    attr_vals.append((a, {"value_number": d}))
                elif a.type == AttributeType.bool:
                    attr_vals.append((a, {"value_bool": bool(_bool(raw))}))
                elif a.type == AttributeType.choice:
                    opt = next((o for o in a.options if o.value.lower() == raw.lower()), None)
                    if opt is None:
                        if dry_run:
                            res.issues.append(
                                Issue(n, ext, f"attr:{code}", f"Вариант «{raw}» будет добавлен в словарь", "warning")
                            )
                            continue
                        opt = AttributeOption(attribute_id=a.id, value=raw, sort=100)
                        session.add(opt)
                        await session.flush()
                        a.options.append(opt)
                        res.issues.append(
                            Issue(n, ext, f"attr:{code}", f"Вариант «{raw}» добавлен в словарь", "warning")
                        )
                    attr_vals.append((a, {"option_id": opt.id}))
                else:
                    attr_vals.append((a, {"value_text": raw[:255]}))
            except ValueError as e:
                errors.append(Issue(n, ext, f"attr:{code}", str(e)))
        if errors:
            res.issues.extend(errors)
            res.failed += 1
            continue

        man = None
        if row.get("manufacturer"):
            man = mans.get(row["manufacturer"].lower())
            if man is None and not dry_run:
                man = Manufacturer(
                    name=row["manufacturer"],
                    slug=_unique(slugify(row["manufacturer"]), {m.slug for m in mans.values()}),
                )
                session.add(man)
                await session.flush()
                mans[man.name.lower()] = man
                res.issues.append(
                    Issue(n, ext, "manufacturer", f"Производитель «{row['manufacturer']}» создан", "warning")
                )
            elif man is None:
                res.issues.append(
                    Issue(n, ext, "manufacturer", f"Производитель «{row['manufacturer']}» будет создан", "warning")
                )

        eq = existing.get(ext)
        created = eq is None
        if created:
            eq = Equipment(external_id=ext, name=name, category_id=cat.id, tariff=None, attribute_values=[], images=[])
            slug = row.get("slug") or slugify(f"{name}-{ext}")
            eq.slug = _unique(slug, used_slugs)
            used_slugs.add(eq.slug)
            session.add(eq)
            existing[ext] = eq
        else:
            eq.name, eq.category_id = name, cat.id
            if row.get("slug") and row["slug"] != eq.slug and row["slug"] not in used_slugs:
                eq.slug = row["slug"]
                used_slugs.add(eq.slug)
        if man is not None or "manufacturer" in row:
            eq.manufacturer_id = man.id if man else None
        if status is not None:
            eq.status_id = status.id
        for key in ("model", "short_description", "description", "terms", "meta_title", "meta_description"):
            if key in row:
                eq.__setattr__(key, row[key] or None)
        for key in ("year", "sort"):
            if values.get(key) is not None:
                setattr(eq, key, values[key])
        for key in ("price_hidden", "is_published", "is_featured"):
            if values.get(key) is not None:
                setattr(eq, key, values[key])
        await session.flush()

        if any(k in row for k in ("price_per_shift", "price_per_day", "shift_hours", "min_units")):
            t = eq.tariff or Tariff(equipment_id=eq.id)
            if eq.tariff is None:
                session.add(t)
                eq.tariff = t
            for key in ("price_per_shift", "price_per_day"):
                if key in row:
                    setattr(t, key, values.get(key))
            if values.get("shift_hours"):
                t.shift_hours = values["shift_hours"]
            if values.get("min_units"):
                t.min_units = values["min_units"]

        by_attr = {v.attribute_id: v for v in eq.attribute_values}
        for a, payload in attr_vals:
            v = by_attr.get(a.id)
            if v is None:
                v = AttributeValue(equipment_id=eq.id, attribute_id=a.id)
                session.add(v)
                eq.attribute_values.append(v)
            v.value_number = v.value_text = v.value_bool = v.option_id = None
            for k, val in payload.items():
                setattr(v, k, val)

        if row.get("images"):
            have = {(img.file or {}).get("key") for img in eq.images}
            for i, fname in enumerate(f.strip() for f in row["images"].split("|") if f.strip()):
                key = f"import/{fname}"
                path = import_dir / fname
                if not path.exists():
                    res.issues.append(
                        Issue(n, ext, "images", f"Файл {fname} не найден в media/public/import", "warning")
                    )
                    continue
                if key in have:
                    continue
                ctype = "image/png" if fname.lower().endswith(".png") else "image/jpeg"
                eq.images.append(
                    EquipmentImage(file=file_record(key, fname, ctype, path.stat().st_size), alt=name, sort=i * 10)
                )
        res.created += created
        res.updated += not created

    if job is not None:
        job.total, job.created, job.updated, job.skipped, job.failed = (
            res.total,
            res.created,
            res.updated,
            res.skipped,
            res.failed,
        )
        job.errors = [i.as_dict() for i in res.issues][:2000]
        job.status = ImportStatus.done
        job.finished_at = datetime.now(UTC)
    return res


def _unique(slug: str, used: set[str]) -> str:
    base = slug or "item"
    s, n = base, 2
    while s in used:
        s = f"{base}-{n}"
        n += 1
    return s


def issues_csv(issues: list[Issue]) -> str:
    buf = io.StringIO()
    buf.write("﻿")
    w = csv.writer(buf, delimiter=";")
    w.writerow(["Строка", "external_id", "Поле", "Уровень", "Сообщение"])
    for i in issues:
        w.writerow([i.row, i.external_id, i.field, "ошибка" if i.level == "error" else "предупреждение", i.message])
    return buf.getvalue()
