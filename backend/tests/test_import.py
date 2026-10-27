import io

import pytest
from sqlalchemy import func, select

from app.core.db import SessionLocal
from app.models import Equipment, Tariff
from app.services import csv_import
from tests.conftest import csrf, login

pytestmark = pytest.mark.usefixtures("seed")

HEAD = "external_id;name;category;manufacturer;model;year;status;price_per_shift;price_per_day;price_hidden;attr:weight;attr:drive;attr:with_operator\n"


def csv_bytes(rows: list[str]) -> bytes:
    return ("﻿" + HEAD + "\n".join(rows) + "\n").encode("utf-8")


async def test_import_creates_updates_and_dedupes():
    rows = [
        "IMP-1;Новый экскаватор;ekskavatory;Komatsu;PC300;2022;available;15000;30000;0;30;Гусеничная;1",
        "EX-KOMATSU-PC200;Komatsu PC200 обновлён;ekskavatory;Komatsu;PC200;2021;available;11000;;0;21;Колёсная;0",
        "IMP-1;Новый экскаватор v2;ekskavatory;Komatsu;PC300;2023;available;16000;32000;0;31;Гусеничная;1",
        "IMP-2;Без категории;no-such;Komatsu;X;2020;;100;;0;;;",
        "IMP-3;Плохой год;katki;Hitachi;R1;abc;available;100;;0;3;;",
        "IMP-4;Новый вариант;ekskavatory;Hitachi;ZX;2020;available;100;;0;5;Шагающая;0",
    ]
    async with SessionLocal() as s:
        res = await csv_import.import_catalog(s, csv_bytes(rows), dry_run=False)
        await s.commit()
    assert (res.total, res.created, res.updated, res.skipped, res.failed) == (6, 2, 1, 1, 2)
    msgs = {(i.external_id, i.field): i.message for i in res.issues}
    assert ("IMP-2", "category") in msgs and ("IMP-3", "year") in msgs
    assert any(i.field == "manufacturer" and "Hitachi" in i.message for i in res.issues)
    assert any(i.field == "attr:drive" and "Шагающая" in i.message for i in res.issues)
    async with SessionLocal() as s:
        e = (await s.execute(select(Equipment).where(Equipment.external_id == "IMP-1"))).scalar_one()
        assert e.name == "Новый экскаватор v2" and e.year == 2023
        t = (await s.execute(select(Tariff).where(Tariff.equipment_id == e.id))).scalar_one()
        assert t.price_per_shift == 16000
        upd = (await s.execute(select(Equipment).where(Equipment.external_id == "EX-KOMATSU-PC200"))).scalar_one()
        assert upd.name == "Komatsu PC200 обновлён" and upd.slug == "ex-komatsu-pc200"
        assert (await s.execute(select(func.count()).select_from(Equipment))).scalar_one() == 6 + 2


async def test_reimport_is_idempotent():
    rows = ["IMP-9;Повтор;katki;JCB;V;2020;available;100;200;0;3;;1"]
    async with SessionLocal() as s:
        await csv_import.import_catalog(s, csv_bytes(rows), dry_run=False)
        await s.commit()
    async with SessionLocal() as s:
        res = await csv_import.import_catalog(s, csv_bytes(rows), dry_run=False)
        await s.commit()
    assert res.created == 0 and res.updated == 1
    async with SessionLocal() as s:
        assert (
            await s.execute(select(func.count()).select_from(Equipment).where(Equipment.external_id == "IMP-9"))
        ).scalar_one() == 1


async def test_missing_required_header():
    async with SessionLocal() as s:
        with pytest.raises(csv_import.HeaderError):
            await csv_import.import_catalog(s, b"name;category\nx;y\n", dry_run=False)


async def test_thousand_rows_with_duplicates_via_api(client):
    import subprocess
    import sys

    from app.models import AvailabilityStatus, Category
    from scripts.gen_import_csv import CATS

    async with SessionLocal() as s:
        have = set((await s.execute(select(Category.slug))).scalars())
        s.add_all([Category(name=c, slug=c) for c in CATS if c not in have])
        s.add(AvailabilityStatus(code="busy", name="Занята", color="orange"))
        await s.commit()

    out = subprocess.run(
        [sys.executable, "-m", "scripts.gen_import_csv", "--rows", "1000", "--duplicates", "50", "--invalid", "20"],
        capture_output=True,
        check=True,
    )
    token = await login(client, "adm@example.com")
    r = await client.post(
        "/api/v1/manager/import",
        headers=csrf(token),
        data={"dry_run": "true"},
        files={"file": ("big.csv", io.BytesIO(out.stdout), "text/csv")},
    )
    assert r.status_code == 201, r.text
    d = r.json()
    assert d["dry_run"] is True and d["total"] == 1070 and d["skipped"] == 50 and d["failed"] >= 1
    async with SessionLocal() as s:
        assert (
            await s.execute(select(func.count()).select_from(Equipment).where(Equipment.external_id.like("IMP-%")))
        ).scalar_one() == 0
    r = await client.post(
        "/api/v1/manager/import", headers=csrf(token), files={"file": ("big.csv", io.BytesIO(out.stdout), "text/csv")}
    )
    assert r.status_code == 201, r.text
    d = r.json()
    assert d["created"] >= 950 and d["updated"] == 0
    async with SessionLocal() as s:
        n = (
            await s.execute(select(func.count()).select_from(Equipment).where(Equipment.external_id.like("IMP-%")))
        ).scalar_one()
    assert n == d["created"]
    r = await client.post(
        "/api/v1/manager/import", headers=csrf(token), files={"file": ("big.csv", io.BytesIO(out.stdout), "text/csv")}
    )
    assert r.json()["created"] == 0 and r.json()["updated"] == d["created"]
    assert (await client.get(f"/api/v1/manager/import/{d['id']}/report.csv")).status_code == 200


async def test_import_requires_admin(client):
    token = await login(client, "m@example.com")
    r = await client.post(
        "/api/v1/manager/import", headers=csrf(token), files={"file": ("x.csv", io.BytesIO(csv_bytes([])), "text/csv")}
    )
    assert r.status_code == 403
