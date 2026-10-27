"""Выборки каталога: карточки, фильтры, фасеты, сравнение (ТЗ 2.2–2.3)."""

from collections import defaultdict
from decimal import Decimal

from sqlalchemy import Select, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.files import file_url
from app.core.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, Paginated, to_int
from app.models import (
    AttributeDefinition,
    AttributeOption,
    AttributeType,
    AttributeValue,
    AvailabilityStatus,
    Category,
    Equipment,
    Manufacturer,
    Tariff,
)
from app.schemas.catalog import (
    AttributeValueOut,
    CategoryOut,
    CompareOut,
    CompareRow,
    EquipmentCard,
    EquipmentDetail,
    FacetAttribute,
    FacetOption,
    Facets,
    ImageOut,
    ManufacturerOut,
    StatusOut,
    TariffOut,
)

EQUIPMENT_LOAD = (
    selectinload(Equipment.category),
    selectinload(Equipment.manufacturer),
    selectinload(Equipment.status),
    selectinload(Equipment.images),
    selectinload(Equipment.tariff),
    selectinload(Equipment.attribute_values).selectinload(AttributeValue.attribute),
    selectinload(Equipment.attribute_values).selectinload(AttributeValue.option),
)

ORDERINGS = {
    "name": (Equipment.name.asc(),),
    "-name": (Equipment.name.desc(),),
    "price": (Tariff.price_per_shift.asc().nulls_last(), Equipment.name.asc()),
    "-price": (Tariff.price_per_shift.desc().nulls_last(), Equipment.name.asc()),
    "new": (Equipment.created_at.desc(),),
    "default": (Equipment.sort.asc(), Equipment.name.asc()),
}


# ---------- сериализация ----------


def category_out(c: Category, count: int = 0) -> CategoryOut:
    return CategoryOut(
        id=c.id,
        name=c.name,
        slug=c.slug,
        parent_id=c.parent_id,
        description=c.description,
        image_url=file_url(c.image),
        is_featured=c.is_featured,
        equipment_count=count,
    )


def manufacturer_out(m: Manufacturer | None) -> ManufacturerOut | None:
    if m is None:
        return None
    return ManufacturerOut(id=m.id, name=m.name, slug=m.slug, logo_url=file_url(m.logo))


def status_out(s: AvailabilityStatus | None) -> StatusOut | None:
    if s is None:
        return None
    return StatusOut(id=s.id, code=s.code, name=s.name, color=s.color, allow_request=s.allow_request)


def tariff_out(t: Tariff | None, hidden: bool) -> TariffOut | None:
    if t is None or hidden:
        return None
    return TariffOut(
        price_per_shift=t.price_per_shift,
        price_per_day=t.price_per_day,
        shift_hours=t.shift_hours,
        min_units=t.min_units,
        note=t.note,
    )


def _raw(av: AttributeValue):
    if av.option is not None:
        return av.option.value
    if av.value_bool is not None:
        return av.value_bool
    if av.value_number is not None:
        return float(av.value_number)
    return av.value_text


def attribute_values_out(e: Equipment) -> list[AttributeValueOut]:
    vals = sorted(e.attribute_values, key=lambda v: (v.attribute.sort, v.attribute.name))
    return [
        AttributeValueOut(
            code=v.attribute.code, name=v.attribute.name, unit=v.attribute.unit, value=v.display, raw=_raw(v)
        )
        for v in vals
    ]


def images_out(e: Equipment) -> list[ImageOut]:
    out = []
    for img in e.images:
        url = file_url(img.file)
        if url:
            out.append(ImageOut(url=url, alt=img.alt or str(e)))
    return out


def equipment_card(e: Equipment) -> EquipmentCard:
    imgs = images_out(e)
    attrs = attribute_values_out(e)
    return EquipmentCard(
        id=e.id,
        slug=e.slug,
        name=e.name,
        model=e.model,
        year=e.year,
        category=category_out(e.category),
        manufacturer=manufacturer_out(e.manufacturer),
        status=status_out(e.status),
        image=imgs[0] if imgs else None,
        short_description=e.short_description,
        price_hidden=e.price_hidden,
        tariff=tariff_out(e.tariff, e.price_hidden),
        is_featured=e.is_featured,
        key_attributes=attrs[:3],
    )


def equipment_detail(e: Equipment) -> EquipmentDetail:
    card = equipment_card(e)
    return EquipmentDetail(
        **card.model_dump(),
        description=e.description,
        terms=e.terms,
        images=images_out(e),
        attributes=attribute_values_out(e),
        meta_title=e.meta_title,
        meta_description=e.meta_description,
        og_image_url=file_url(e.og_image),
        noindex=e.noindex,
    )


# ---------- фильтры ----------


async def category_with_children_ids(session: AsyncSession, slug: str) -> tuple[Category | None, list[int]]:
    cat = (await session.execute(select(Category).where(Category.slug == slug))).scalar_one_or_none()
    if cat is None:
        return None, []
    children = (await session.execute(select(Category.id).where(Category.parent_id == cat.id))).scalars().all()
    return cat, [cat.id, *children]


def _split(value: str | None) -> list[str]:
    return [v.strip() for v in (value or "").split(",") if v.strip()]


async def apply_filters(session: AsyncSession, stmt: Select, params: dict[str, str]) -> Select:
    stmt = stmt.where(Equipment.is_published.is_(True))
    if slug := params.get("category"):
        _, ids = await category_with_children_ids(session, slug)
        stmt = stmt.where(Equipment.category_id.in_(ids or [-1]))
    if mans := _split(params.get("manufacturer")):
        stmt = stmt.where(Equipment.manufacturer_id.in_(select(Manufacturer.id).where(Manufacturer.slug.in_(mans))))
    if statuses := _split(params.get("status")):
        stmt = stmt.where(
            Equipment.status_id.in_(select(AvailabilityStatus.id).where(AvailabilityStatus.code.in_(statuses)))
        )
    if (q := (params.get("q") or "").strip()) and len(q) <= 100:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Equipment.name.ilike(like),
                Equipment.model.ilike(like),
                func.word_similarity(q, func.concat(Equipment.name, " ", func.coalesce(Equipment.model, ""))) > 0.4,
            )
        )
    attr_params = {k: v for k, v in params.items() if k.startswith("attr_") and v}
    if attr_params:
        codes = {k[5:].removesuffix("_min").removesuffix("_max") for k in attr_params}
        attrs = (
            (
                await session.execute(
                    select(AttributeDefinition).where(
                        AttributeDefinition.code.in_(codes), AttributeDefinition.is_filterable.is_(True)
                    )
                )
            )
            .scalars()
            .all()
        )
        for attr in attrs:
            base = select(AttributeValue.id).where(
                AttributeValue.equipment_id == Equipment.id, AttributeValue.attribute_id == attr.id
            )
            cond = None
            if attr.type == AttributeType.choice and (vals := _split(attr_params.get(f"attr_{attr.code}"))):
                cond = base.where(
                    AttributeValue.option_id.in_(select(AttributeOption.id).where(AttributeOption.value.in_(vals)))
                )
            elif attr.type == AttributeType.number:
                lo = _dec(attr_params.get(f"attr_{attr.code}_min"))
                hi = _dec(attr_params.get(f"attr_{attr.code}_max"))
                if lo is not None or hi is not None:
                    cond = base
                    if lo is not None:
                        cond = cond.where(AttributeValue.value_number >= lo)
                    if hi is not None:
                        cond = cond.where(AttributeValue.value_number <= hi)
            elif attr.type == AttributeType.bool and (v := attr_params.get(f"attr_{attr.code}")):
                cond = base.where(AttributeValue.value_bool.is_(v.lower() in ("1", "true", "yes", "да")))
            elif attr.type == AttributeType.string and (v := attr_params.get(f"attr_{attr.code}")):
                cond = base.where(AttributeValue.value_text.ilike(v))
            if cond is not None:
                stmt = stmt.where(exists(cond))
    return stmt


def _dec(v: str | None) -> Decimal | None:
    if v is None:
        return None
    try:
        return Decimal(str(v).replace(",", ".").strip())
    except Exception:
        return None


async def list_equipment(session: AsyncSession, params: dict[str, str]) -> Paginated[EquipmentCard]:
    page = to_int(params.get("page"), 1, 1)
    page_size = to_int(params.get("page_size"), DEFAULT_PAGE_SIZE, 1, MAX_PAGE_SIZE)
    ordering = ORDERINGS.get(params.get("ordering") or "default", ORDERINGS["default"])

    stmt = select(Equipment)
    stmt = await apply_filters(session, stmt, params)
    if params.get("ordering") in ("price", "-price"):
        stmt = stmt.outerjoin(Tariff, Tariff.equipment_id == Equipment.id)
    total = (await session.execute(select(func.count()).select_from(stmt.order_by(None).subquery()))).scalar_one()
    pages = max((total + page_size - 1) // page_size, 1)
    page = min(page, pages)
    rows = (
        (
            await session.execute(
                stmt.options(*EQUIPMENT_LOAD).order_by(*ordering).offset((page - 1) * page_size).limit(page_size)
            )
        )
        .scalars()
        .unique()
        .all()
    )
    return Paginated(items=[equipment_card(e) for e in rows], page=page, page_size=page_size, total=total, pages=pages)


async def get_equipment(session: AsyncSession, slug: str) -> Equipment | None:
    return (
        await session.execute(
            select(Equipment).options(*EQUIPMENT_LOAD).where(Equipment.slug == slug, Equipment.is_published.is_(True))
        )
    ).scalar_one_or_none()


async def list_categories(session: AsyncSession) -> list[CategoryOut]:
    counts = dict(
        (
            await session.execute(
                select(Equipment.category_id, func.count(Equipment.id))
                .where(Equipment.is_published.is_(True))
                .group_by(Equipment.category_id)
            )
        ).all()
    )
    cats = (
        (
            await session.execute(
                select(Category).where(Category.is_published.is_(True)).order_by(Category.sort, Category.name)
            )
        )
        .scalars()
        .all()
    )
    totals: dict[int, int] = defaultdict(int)
    for c in cats:
        totals[c.id] += counts.get(c.id, 0)
        if c.parent_id:
            totals[c.parent_id] += counts.get(c.id, 0)
    return [category_out(c, totals[c.id]) for c in cats]


async def facets(session: AsyncSession, params: dict[str, str]) -> Facets:
    """Фасеты считаются по категории (без остальных фильтров) — просто и предсказуемо."""
    base_params = {"category": params.get("category", "")}
    base = await apply_filters(session, select(Equipment.id), base_params)
    base_ids = base.subquery()

    mans = (
        await session.execute(
            select(Manufacturer.slug, Manufacturer.name, func.count(Equipment.id))
            .join(Equipment, Equipment.manufacturer_id == Manufacturer.id)
            .where(Equipment.id.in_(select(base_ids.c.id)))
            .group_by(Manufacturer.id)
            .order_by(Manufacturer.sort, Manufacturer.name)
        )
    ).all()
    statuses = (
        await session.execute(
            select(AvailabilityStatus.code, AvailabilityStatus.name, func.count(Equipment.id))
            .join(Equipment, Equipment.status_id == AvailabilityStatus.id)
            .where(Equipment.id.in_(select(base_ids.c.id)))
            .group_by(AvailabilityStatus.id)
            .order_by(AvailabilityStatus.sort)
        )
    ).all()
    categories = [
        FacetOption(value=c.slug, label=c.name, count=c.equipment_count)
        for c in await list_categories(session)
        if c.parent_id is None
    ]

    attr_stmt = (
        select(AttributeDefinition)
        .where(AttributeDefinition.is_filterable.is_(True))
        .options(selectinload(AttributeDefinition.options))
    )
    if slug := params.get("category"):
        cat, _ = await category_with_children_ids(session, slug)
        if cat is not None:
            root_id = cat.parent_id or cat.id
            attr_stmt = attr_stmt.join(AttributeDefinition.categories).where(Category.id.in_([cat.id, root_id]))
    attrs = (await session.execute(attr_stmt.order_by(AttributeDefinition.sort))).scalars().unique().all()

    out_attrs: list[FacetAttribute] = []
    for a in attrs:
        fa = FacetAttribute(code=a.code, name=a.name, unit=a.unit, type=a.type.value)
        if a.type == AttributeType.choice:
            rows = (
                await session.execute(
                    select(AttributeOption.value, func.count(AttributeValue.id))
                    .join(AttributeValue, AttributeValue.option_id == AttributeOption.id)
                    .where(AttributeOption.attribute_id == a.id, AttributeValue.equipment_id.in_(select(base_ids.c.id)))
                    .group_by(AttributeOption.id)
                    .order_by(AttributeOption.sort)
                )
            ).all()
            fa.options = [FacetOption(value=v, label=v, count=n) for v, n in rows]
        elif a.type == AttributeType.number:
            lo, hi = (
                await session.execute(
                    select(func.min(AttributeValue.value_number), func.max(AttributeValue.value_number)).where(
                        AttributeValue.attribute_id == a.id, AttributeValue.equipment_id.in_(select(base_ids.c.id))
                    )
                )
            ).one()
            fa.min, fa.max = lo, hi
        elif a.type == AttributeType.bool:
            n = (
                await session.execute(
                    select(func.count(AttributeValue.id)).where(
                        AttributeValue.attribute_id == a.id,
                        AttributeValue.value_bool.is_(True),
                        AttributeValue.equipment_id.in_(select(base_ids.c.id)),
                    )
                )
            ).scalar_one()
            fa.options = [FacetOption(value="true", label="Да", count=n)]
        if fa.options or fa.min is not None:
            out_attrs.append(fa)

    return Facets(
        manufacturers=[FacetOption(value=s, label=n, count=c) for s, n, c in mans],
        statuses=[FacetOption(value=s, label=n, count=c) for s, n, c in statuses],
        categories=categories,
        attributes=out_attrs,
    )


async def compare(session: AsyncSession, ids: list[int]) -> CompareOut:
    rows = (
        (
            await session.execute(
                select(Equipment)
                .options(*EQUIPMENT_LOAD)
                .where(Equipment.id.in_(ids), Equipment.is_published.is_(True))
            )
        )
        .scalars()
        .unique()
        .all()
    )
    by_id = {e.id: e for e in rows}
    ordered = [by_id[i] for i in ids if i in by_id]
    cards = [equipment_card(e) for e in ordered]

    fixed = [
        CompareRow(
            code="manufacturer",
            name="Производитель",
            values=[e.manufacturer.name if e.manufacturer else None for e in ordered],
        ),
        CompareRow(code="model", name="Модель", values=[e.model for e in ordered]),
        CompareRow(code="year", name="Год выпуска", values=[str(e.year) if e.year else None for e in ordered]),
        CompareRow(code="status", name="Доступность", values=[e.status.name if e.status else None for e in ordered]),
        CompareRow(
            code="price_per_shift",
            name="Тариф за смену",
            unit="₽",
            values=[
                None
                if (e.price_hidden or not e.tariff or e.tariff.price_per_shift is None)
                else f"{e.tariff.price_per_shift:.0f}"
                for e in ordered
            ],
        ),
        CompareRow(
            code="price_per_day",
            name="Тариф за сутки",
            unit="₽",
            values=[
                None
                if (e.price_hidden or not e.tariff or e.tariff.price_per_day is None)
                else f"{e.tariff.price_per_day:.0f}"
                for e in ordered
            ],
        ),
    ]
    attr_defs: dict[str, AttributeDefinition] = {}
    for e in ordered:
        for v in e.attribute_values:
            if v.attribute.is_comparable:
                attr_defs[v.attribute.code] = v.attribute
    dyn = []
    for code, a in sorted(attr_defs.items(), key=lambda kv: (kv[1].sort, kv[1].name)):
        values = []
        for e in ordered:
            m = next((v for v in e.attribute_values if v.attribute.code == code), None)
            values.append(m.display if m else None)
        dyn.append(CompareRow(code=code, name=a.name, unit=a.unit, values=values))
    return CompareOut(items=cards, rows=fixed + dyn)
