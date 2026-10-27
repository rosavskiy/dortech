"""Предварительный расчёт стоимости (ТЗ 3.2). Выполняется только на сервере."""

from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Equipment, ExtraService, PricingSettings, RateUnit
from app.schemas.inquiries import EstimateExtra, EstimateIn, EstimateLine, EstimateOut


@dataclass
class Settings:
    rounding_step: int = 1
    vat_label: str = "без НДС"
    disclaimer: str = "Расчёт предварительный и не является офертой."
    extra: dict = field(default_factory=dict)


async def get_pricing_settings(session: AsyncSession) -> PricingSettings:
    ps = (await session.execute(select(PricingSettings).limit(1))).scalar_one_or_none()
    if ps is None:
        ps = PricingSettings()
        session.add(ps)
        await session.flush()
    return ps


def round_money(value: Decimal, step: int) -> Decimal:
    step = max(int(step or 1), 1)
    q = Decimal(step)
    return (value / q).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * q


def default_units(period_from: date | None, period_to: date | None) -> int:
    if period_from and period_to and period_to >= period_from:
        return (period_to - period_from).days + 1
    return 1


async def estimate(session: AsyncSession, data: EstimateIn) -> EstimateOut:
    ps = await get_pricing_settings(session)
    ids = [i.equipment_id for i in data.items]
    rows = (
        (await session.execute(select(Equipment).options(selectinload(Equipment.tariff)).where(Equipment.id.in_(ids))))
        .scalars()
        .all()
    )
    by_id = {e.id: e for e in rows}
    base_units = default_units(data.period_from, data.period_to)

    lines: list[EstimateLine] = []
    total = Decimal("0")
    partial = False
    for item in data.items:
        eq = by_id.get(item.equipment_id)
        if eq is None or not eq.is_published:
            continue
        units = item.units or base_units
        tariff = eq.tariff
        price: Decimal | None = None
        if tariff is not None and not eq.price_hidden:
            price = tariff.price_per_shift if item.unit == RateUnit.shift else tariff.price_per_day
        line_total: Decimal | None = None
        needs_quote = price is None
        if price is not None:
            min_units = tariff.min_units if tariff else 1
            line_total = round_money(Decimal(price) * max(units, min_units) * item.quantity, ps.rounding_step)
            total += line_total
        else:
            partial = True
        lines.append(
            EstimateLine(
                equipment_id=eq.id,
                name=eq.name,
                model=eq.model,
                quantity=item.quantity,
                units=units,
                unit=item.unit,
                unit_price=price,
                line_total=line_total,
                needs_quote=needs_quote,
            )
        )

    extras: list[EstimateExtra] = []
    if data.extra_service_ids:
        services = (
            (
                await session.execute(
                    select(ExtraService).where(
                        ExtraService.id.in_(data.extra_service_ids), ExtraService.is_active.is_(True)
                    )
                )
            )
            .scalars()
            .all()
        )
        for s in services:
            extras.append(EstimateExtra(id=s.id, name=s.name, price=s.price))
            total += Decimal(s.price)

    return EstimateOut(
        lines=lines,
        extras=extras,
        total=round_money(total, ps.rounding_step),
        is_partial=partial,
        vat_label=ps.vat_label,
        disclaimer=ps.disclaimer_text,
        rounding_step=ps.rounding_step,
    )
