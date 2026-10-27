from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import get_session
from app.core.deps import client_ip, csrf_protect, require_admin
from app.models import ImportJob, ImportStatus, User
from app.services import csv_import
from app.services.audit import log_action

router = APIRouter(prefix="/manager/import", tags=["import"], dependencies=[Depends(csrf_protect)])


def job_out(j: ImportJob) -> dict:
    return {
        "id": j.id,
        "file_name": j.file_name,
        "dry_run": j.dry_run,
        "status": j.status.value,
        "total": j.total,
        "created": j.created,
        "updated": j.updated,
        "skipped": j.skipped,
        "failed": j.failed,
        "warnings": sum(1 for e in (j.errors or []) if e.get("level") == "warning"),
        "errors": j.errors or [],
        "created_at": j.created_at,
        "finished_at": j.finished_at,
        "started_by": str(j.started_by) if j.started_by else None,
    }


@router.get("")
async def jobs(user: User = Depends(require_admin), session: AsyncSession = Depends(get_session)) -> list[dict]:
    rows = (
        (
            await session.execute(
                select(ImportJob).options(selectinload(ImportJob.started_by)).order_by(ImportJob.id.desc()).limit(50)
            )
        )
        .scalars()
        .all()
    )
    return [{**job_out(j), "errors": []} for j in rows]


@router.post("", status_code=201)
async def run_import(
    request: Request,
    file: UploadFile,
    dry_run: bool = Form(False),
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    data = await file.read()
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(400, "Файл больше 20 МБ")
    user = await session.merge(user)
    job = ImportJob(
        file_name=(file.filename or "import.csv")[:255],
        dry_run=dry_run,
        started_by=user,
        status=ImportStatus.pending,
    )
    session.add(job)
    await session.flush()
    try:
        await csv_import.import_catalog(session, data, dry_run=dry_run, job=job)
    except csv_import.HeaderError as e:
        await session.rollback()
        raise HTTPException(400, str(e)) from e
    except UnicodeDecodeError as e:
        await session.rollback()
        raise HTTPException(400, "Файл должен быть в кодировке UTF-8") from e
    if dry_run:
        snapshot = job_out(job)
        await session.rollback()
        async with session.begin():
            j2 = ImportJob(
                file_name=job.file_name,
                dry_run=True,
                started_by=user,
                status=ImportStatus.done,
                total=job.total,
                created=job.created,
                updated=job.updated,
                skipped=job.skipped,
                failed=job.failed,
                errors=job.errors,
                finished_at=job.finished_at,
            )
            session.add(j2)
        snapshot["id"] = j2.id
        return snapshot
    log_action(
        session,
        actor=user,
        action="catalog.import",
        target=job,
        changes={"created": job.created, "updated": job.updated, "failed": job.failed},
        ip=client_ip(request),
    )
    await session.commit()
    await session.refresh(job)
    return job_out(job)


@router.get("/{job_id}")
async def job(job_id: int, user: User = Depends(require_admin), session: AsyncSession = Depends(get_session)) -> dict:
    j = (
        await session.execute(
            select(ImportJob).options(selectinload(ImportJob.started_by)).where(ImportJob.id == job_id)
        )
    ).scalar_one_or_none()
    if j is None:
        raise HTTPException(404, "Импорт не найден")
    return job_out(j)


@router.get("/{job_id}/report.csv", response_class=PlainTextResponse)
async def report(job_id: int, user: User = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    j = await session.get(ImportJob, job_id)
    if j is None:
        raise HTTPException(404, "Импорт не найден")
    issues = [
        csv_import.Issue(**{k: e[k] for k in ("row", "external_id", "field", "message", "level")})
        for e in (j.errors or [])
    ]
    return PlainTextResponse(
        csv_import.issues_csv(issues),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="import-{job_id}-report.csv"'},
    )


@router.get("/template.csv", response_class=PlainTextResponse)
async def template(user: User = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    from app.models import AttributeDefinition

    codes = (await session.execute(select(AttributeDefinition.code).order_by(AttributeDefinition.sort))).scalars().all()
    head = [
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
        *[f"attr:{c}" for c in codes],
    ]
    example = [
        "EX-001",
        "Экскаватор Komatsu PC200",
        "",
        "ekskavatory",
        "Komatsu",
        "PC200",
        "2021",
        "available",
        "Гусеничный экскаватор 20 т",
        "",
        "",
        "12000",
        "28000",
        "8",
        "1",
        "0",
        "1",
        "0",
        "100",
        "pc200-1.jpg|pc200-2.jpg",
        "",
        "",
        *["" for _ in codes],
    ]
    return PlainTextResponse(
        "﻿" + ";".join(head) + "\n" + ";".join(example) + "\n",
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="catalog-template.csv"'},
    )
