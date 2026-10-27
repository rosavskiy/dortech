"""Тесты выполняются против отдельной БД dortech_test (PostgreSQL), миграции применяются один раз."""

import os
import subprocess
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://dortech:dortech@localhost:5432/dortech_test")
os.environ["RATE_LIMIT_ENABLED"] = "0"
os.environ["ENVIRONMENT"] = "test"
os.environ["NOTIFICATION_EMAILS"] = "managers@example.com"

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.db import SessionLocal, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402
    AttributeDefinition,
    AttributeOption,
    AttributeType,
    AttributeValue,
    AvailabilityStatus,
    Category,
    Equipment,
    ExtraService,
    Manufacturer,
    Organization,
    PricingSettings,
    Role,
    Tariff,
    User,
)

PASSWORD = "Secret123"


@pytest.fixture(scope="session", autouse=True)
def _migrate():
    env = {**os.environ, "DATABASE_URL": os.environ["DATABASE_URL"]}
    subprocess.run(
        ["alembic", "upgrade", "head"],
        check=True,
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env=env,
        capture_output=True,
    )


@pytest.fixture(autouse=True)
async def _clean_db():
    async with engine.begin() as conn:
        tables = (
            (
                await conn.execute(
                    text("select tablename from pg_tables where schemaname='public' and tablename <> 'alembic_version'")
                )
            )
            .scalars()
            .all()
        )
        await conn.execute(text("TRUNCATE " + ", ".join(f'"{t}"' for t in tables) + " RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
async def seed():
    """Контрольный набор: 2 категории, 2 производителя, статусы, характеристики, 6 карточек, тарифы, услуги, пользователи."""
    async with SessionLocal() as s:
        s.add(PricingSettings(id=1, rounding_step=10))
        st_av = AvailabilityStatus(code="available", name="В наличии", color="green", allow_request=True, sort=1)
        st_req = AvailabilityStatus(code="on_request", name="Под заказ", color="gray", allow_request=True, sort=2)
        s.add_all([st_av, st_req])
        a_w = AttributeDefinition(
            code="weight", name="Масса", unit="т", type=AttributeType.number, is_filterable=True, sort=1
        )
        a_d = AttributeDefinition(code="drive", name="Ходовая", type=AttributeType.choice, is_filterable=True, sort=2)
        a_o = AttributeDefinition(
            code="with_operator", name="С машинистом", type=AttributeType.bool, is_filterable=True, sort=3
        )
        s.add_all([a_w, a_d, a_o])
        c1 = Category(name="Экскаваторы", slug="ekskavatory", sort=1, attributes=[a_w, a_d, a_o])
        c2 = Category(name="Катки", slug="katki", sort=2, attributes=[a_w, a_o])
        m1 = Manufacturer(name="Komatsu", slug="komatsu", sort=1)
        m2 = Manufacturer(name="JCB", slug="jcb", sort=2)
        s.add_all([c1, c2, m1, m2])
        await s.flush()
        o_track = AttributeOption(attribute_id=a_d.id, value="Гусеничная", sort=1)
        o_wheel = AttributeOption(attribute_id=a_d.id, value="Колёсная", sort=2)
        s.add_all([o_track, o_wheel])
        await s.flush()
        spec = [
            # slug, name, model, cat, man, status, weight, drive, operator, price_shift, hidden, published
            (
                "ex-komatsu-pc200",
                "Экскаватор Komatsu PC200",
                "PC200",
                c1,
                m1,
                st_av,
                20,
                o_track,
                True,
                10000,
                False,
                True,
            ),
            (
                "ex-komatsu-pw160",
                "Экскаватор Komatsu PW160",
                "PW160",
                c1,
                m1,
                st_av,
                16,
                o_wheel,
                False,
                9000,
                False,
                True,
            ),
            ("ex-jcb-js220", "Экскаватор JCB JS220", "JS220", c1, m2, st_req, 22, o_track, True, 12000, False, True),
            ("ex-jcb-3cx", "Экскаватор JCB 3CX", "3CX", c1, m2, st_av, 8, o_wheel, True, None, True, True),
            ("roller-jcb-vmt", "Каток JCB VMT", "VMT", c2, m2, st_av, 3, None, False, 5000, False, True),
            ("ex-hidden", "Скрытый экскаватор", "X", c1, m1, st_av, 1, None, False, 1, False, False),
        ]
        eqs = {}
        for slug, name, model, cat, man, st, w, drive, op, price, hidden, pub in spec:
            e = Equipment(
                name=name,
                slug=slug,
                model=model,
                category_id=cat.id,
                manufacturer_id=man.id,
                status_id=st.id,
                external_id=slug.upper(),
                price_hidden=hidden,
                is_published=pub,
                year=2020,
            )
            s.add(e)
            await s.flush()
            if price is not None:
                s.add(
                    Tariff(
                        equipment_id=e.id, price_per_shift=Decimal(price), price_per_day=Decimal(price) * 2, min_units=1
                    )
                )
            s.add(AttributeValue(equipment_id=e.id, attribute_id=a_w.id, value_number=Decimal(w)))
            if drive is not None:
                s.add(AttributeValue(equipment_id=e.id, attribute_id=a_d.id, option_id=drive.id))
            s.add(AttributeValue(equipment_id=e.id, attribute_id=a_o.id, value_bool=op))
            eqs[slug] = e
        s.add(ExtraService(id=1, name="Доставка", price=Decimal("15000"), is_active=True, sort=1))
        org_a = Organization(name="ООО «А»", inn="1111111111")
        org_b = Organization(name="ООО «Б»", inn="2222222222")
        s.add_all([org_a, org_b])
        await s.flush()
        now = datetime.now(UTC)
        users = {
            "a": User(
                email="a@example.com",
                password_hash=hash_password(PASSWORD),
                first_name="Анна",
                last_name="А",
                role=Role.client,
                organization_id=org_a.id,
                email_confirmed_at=now,
            ),
            "b": User(
                email="b@example.com",
                password_hash=hash_password(PASSWORD),
                first_name="Борис",
                last_name="Б",
                role=Role.client,
                organization_id=org_b.id,
                email_confirmed_at=now,
            ),
            "manager": User(
                email="m@example.com",
                password_hash=hash_password(PASSWORD),
                first_name="Мария",
                last_name="М",
                role=Role.manager,
                email_confirmed_at=now,
            ),
            "admin": User(
                email="adm@example.com",
                password_hash=hash_password(PASSWORD),
                first_name="Админ",
                last_name="А",
                role=Role.admin,
                email_confirmed_at=now,
            ),
            "unconfirmed": User(
                email="u@example.com",
                password_hash=hash_password(PASSWORD),
                first_name="Ул",
                last_name="У",
                role=Role.client,
                organization_id=org_a.id,
            ),
        }
        s.add_all(users.values())
        await s.commit()
        return {
            "equipment": {k: v.id for k, v in eqs.items()},
            "org_a": org_a.id,
            "org_b": org_b.id,
            "users": {k: u.id for k, u in users.items()},
        }


async def login(client: AsyncClient, email: str, password: str = PASSWORD) -> str:
    """Входит и возвращает CSRF-токен; cookie сохраняется в клиенте."""
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["csrf_token"]


def csrf(token: str) -> dict:
    return {"X-CSRF-Token": token}


async def create_inquiry(
    client: AsyncClient, equipment_id: int, *, token: str | None = None, via_account: bool = False, **extra
) -> dict:
    body = {
        "items": [{"equipment_id": equipment_id, "quantity": 1, "unit": "shift", "units": 2}],
        "extra_service_ids": [],
        "contact_name": "Тест Тестов",
        "contact_phone": "+79000000000",
        "contact_email": "t@example.com",
        "consent": True,
        **extra,
    }
    url = "/api/v1/account/inquiries" if via_account else "/api/v1/inquiries"
    r = await client.post(url, json=body, headers=csrf(token) if token else {})
    assert r.status_code == 201, r.text
    return r.json()
