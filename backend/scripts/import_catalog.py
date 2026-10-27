"""CLI-импорт каталога: uv run python -m scripts.import_catalog file.csv [--dry-run]"""

import argparse
import asyncio
from pathlib import Path

from app.core.db import SessionLocal
from app.models import ImportJob, ImportStatus
from app.services import csv_import


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    data = Path(args.file).read_bytes()
    async with SessionLocal() as s:
        job = ImportJob(file_name=Path(args.file).name, dry_run=args.dry_run, status=ImportStatus.pending)
        s.add(job)
        await s.flush()
        res = await csv_import.import_catalog(s, data, dry_run=args.dry_run, job=job)
        if args.dry_run:
            await s.rollback()
        else:
            await s.commit()
    print(
        f"строк: {res.total}, создано: {res.created}, обновлено: {res.updated}, пропущено: {res.skipped}, с ошибками: {res.failed}"
    )
    for i in res.issues[:50]:
        print(f"  [{i.level}] строка {i.row} {i.external_id} {i.field}: {i.message}")
    if res.errors:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
