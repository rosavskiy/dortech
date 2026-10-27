from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.pagination import Paginated
from app.models import AvailabilityStatus, Manufacturer
from app.schemas.catalog import (
    CategoryOut,
    CompareOut,
    EquipmentCard,
    EquipmentDetail,
    Facets,
    ManufacturerOut,
    StatusOut,
)
from app.services import catalog as svc

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/categories", response_model=list[CategoryOut])
async def categories(session: AsyncSession = Depends(get_session)):
    return await svc.list_categories(session)


@router.get("/manufacturers", response_model=list[ManufacturerOut])
async def manufacturers(session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(select(Manufacturer).order_by(Manufacturer.sort, Manufacturer.name))).scalars().all()
    return [svc.manufacturer_out(m) for m in rows]


@router.get("/statuses", response_model=list[StatusOut])
async def statuses(session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(select(AvailabilityStatus).order_by(AvailabilityStatus.sort))).scalars().all()
    return [svc.status_out(s) for s in rows]


@router.get("/facets", response_model=Facets)
async def facets(request: Request, session: AsyncSession = Depends(get_session)):
    return await svc.facets(session, dict(request.query_params))


@router.get("/equipment", response_model=Paginated[EquipmentCard])
async def equipment_list(request: Request, session: AsyncSession = Depends(get_session)):
    return await svc.list_equipment(session, dict(request.query_params))


@router.get("/equipment/{slug}", response_model=EquipmentDetail)
async def equipment_detail(slug: str, session: AsyncSession = Depends(get_session)):
    e = await svc.get_equipment(session, slug)
    if e is None:
        raise HTTPException(404, "Техника не найдена")
    return svc.equipment_detail(e)


@router.get("/compare", response_model=CompareOut)
async def compare(ids: str = "", session: AsyncSession = Depends(get_session)):
    parsed: list[int] = []
    for part in ids.split(","):
        part = part.strip()
        if part.isdigit() and int(part) not in parsed:
            parsed.append(int(part))
    if len(parsed) > 4:
        raise HTTPException(400, "Сравнивать можно не более четырёх карточек")
    return await svc.compare(session, parsed)
