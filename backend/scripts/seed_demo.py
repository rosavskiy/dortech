"""Демо-данные (идемпотентно). Запуск: uv run python -m scripts.seed_demo
Пользователи: admin@dortech-demo.ru / manager@dortech-demo.ru / client-a@dortech-demo.ru / client-b@dortech-demo.ru, пароль Dortech2026!"""

import asyncio
import random
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from faker import Faker
from PIL import Image, ImageDraw, ImageFont
from slugify import slugify
from sqlalchemy import select

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.files import file_record
from app.core.security import hash_password
from app.models import (
    AttributeDefinition,
    AttributeOption,
    AttributeType,
    AttributeValue,
    AvailabilityStatus,
    Category,
    Equipment,
    EquipmentImage,
    ExtraService,
    Inquiry,
    InquirySource,
    Manufacturer,
    Organization,
    Page,
    PricingSettings,
    Project,
    Publication,
    Role,
    Service,
    SiteSettings,
    Tariff,
    User,
)
from app.schemas.inquiries import EstimateItemIn, InquiryCreateIn
from app.services.inquiries import create_inquiry

fake = Faker("ru_RU")
random.seed(42)
Faker.seed(42)
PASSWORD = "Dortech2026!"

CATEGORIES = [
    ("Экскаваторы", "ekskavatory", "Гусеничные и колёсные экскаваторы от 1,5 до 50 т", "#3b6ea5"),
    ("Погрузчики", "pogruzchiki", "Фронтальные и телескопические погрузчики", "#d97706"),
    ("Автокраны", "avtokrany", "Автокраны грузоподъёмностью 16–100 т", "#b45309"),
    ("Самосвалы", "samosvaly", "Самосвалы 10–40 т для перевозки сыпучих грузов", "#4b5563"),
    ("Бульдозеры", "buldozery", "Бульдозеры для планировки и перемещения грунта", "#7c3aed"),
    ("Катки", "katki", "Дорожные катки грунтовые и асфальтовые", "#0f766e"),
    ("Автогрейдеры", "avtogreydery", "Автогрейдеры для профилирования дорог", "#9333ea"),
    ("Манипуляторы", "manipulyatory", "Краны-манипуляторы на шасси", "#be123c"),
]
MANUFACTURERS = [
    "Komatsu",
    "Hitachi",
    "Caterpillar",
    "JCB",
    "Volvo",
    "Liebherr",
    "XCMG",
    "SANY",
    "КАМАЗ",
    "МАЗ",
    "Hyundai",
    "Doosan",
]
STATUSES = [
    ("available", "В наличии", "green", True, 10),
    ("busy", "Занята", "orange", True, 20),
    ("on_request", "Под заказ", "gray", True, 30),
]
ATTRIBUTES = [
    ("weight", "Эксплуатационная масса", "т", AttributeType.number, True, 10),
    ("engine_power", "Мощность двигателя", "л.с.", AttributeType.number, True, 20),
    ("bucket_volume", "Объём ковша", "м³", AttributeType.number, True, 30),
    ("lifting_capacity", "Грузоподъёмность", "т", AttributeType.number, True, 40),
    ("boom_length", "Длина стрелы", "м", AttributeType.number, True, 50),
    ("drive", "Ходовая часть", None, AttributeType.choice, True, 60),
    ("fuel", "Топливо", None, AttributeType.choice, True, 70),
    ("with_operator", "С машинистом", None, AttributeType.bool, True, 80),
]
ATTR_OPTIONS = {"drive": ["Гусеничная", "Колёсная"], "fuel": ["Дизель", "Электро"]}
CATEGORY_ATTRS = {
    "ekskavatory": ["weight", "engine_power", "bucket_volume", "drive", "fuel", "with_operator"],
    "pogruzchiki": ["weight", "engine_power", "bucket_volume", "lifting_capacity", "drive", "with_operator"],
    "avtokrany": ["weight", "lifting_capacity", "boom_length", "with_operator"],
    "samosvaly": ["weight", "engine_power", "lifting_capacity", "with_operator"],
    "buldozery": ["weight", "engine_power", "drive", "with_operator"],
    "katki": ["weight", "engine_power", "with_operator"],
    "avtogreydery": ["weight", "engine_power", "with_operator"],
    "manipulyatory": ["weight", "lifting_capacity", "boom_length", "with_operator"],
}
SINGULAR = {
    "ekskavatory": "Экскаватор",
    "pogruzchiki": "Погрузчик",
    "avtokrany": "Автокран",
    "samosvaly": "Самосвал",
    "buldozery": "Бульдозер",
    "katki": "Каток",
    "avtogreydery": "Автогрейдер",
    "manipulyatory": "Манипулятор",
}
MODELS = [
    "PC200",
    "ZX210",
    "320D",
    "3CX",
    "EC220",
    "R924",
    "XE215",
    "SY215",
    "6520",
    "5516",
    "R220",
    "DX225",
    "WB97",
    "L120",
    "KS-55713",
    "QY50",
    "D65",
    "BW213",
    "GR215",
    "F5",
]


def placeholder(path, text: str, color: str, size=(1200, 800)) -> int:
    img = Image.new("RGB", size, color)
    d = ImageDraw.Draw(img)
    font = None
    for f in (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
        try:
            font = ImageFont.truetype(f, 64)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default(size=48)
    d.rectangle([40, 40, size[0] - 40, size[1] - 40], outline="white", width=6)
    bbox = d.textbbox((0, 0), text, font=font)
    d.text(((size[0] - bbox[2]) / 2, (size[1] - bbox[3]) / 2), text, fill="white", font=font)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "JPEG", quality=80)
    return path.stat().st_size


async def get_or_create(session, model, defaults=None, **kw):
    obj = (await session.execute(select(model).filter_by(**kw))).scalar_one_or_none()
    created = False
    if obj is None:
        obj = model(**kw, **(defaults or {}))
        session.add(obj)
        await session.flush()
        created = True
    return obj, created


async def seed() -> None:
    public = settings.media_root / "public"
    async with SessionLocal() as s:
        # справочники
        statuses = {}
        for code, name, color, allow, sort in STATUSES:
            statuses[code], _ = await get_or_create(
                s, AvailabilityStatus, {"name": name, "color": color, "allow_request": allow, "sort": sort}, code=code
            )
        attrs = {}
        for code, name, unit, typ, filt, sort in ATTRIBUTES:
            attrs[code], _ = await get_or_create(
                s,
                AttributeDefinition,
                {"name": name, "unit": unit, "type": typ, "is_filterable": filt, "sort": sort},
                code=code,
            )
        options = {}
        for code, values in ATTR_OPTIONS.items():
            for i, v in enumerate(values):
                options[(code, v)], _ = await get_or_create(
                    s, AttributeOption, {"sort": i * 10}, attribute_id=attrs[code].id, value=v
                )
        cats = {}
        for i, (name, slug, desc, color) in enumerate(CATEGORIES):
            cat, created = await get_or_create(
                s, Category, {"name": name, "description": desc, "sort": (i + 1) * 10, "is_featured": True}, slug=slug
            )
            if created:
                size = placeholder(public / "categories" / f"{slug}.jpg", name, color, (800, 600))
                cat.image = file_record(f"categories/{slug}.jpg", f"{slug}.jpg", "image/jpeg", size)
            await s.refresh(cat, ["attributes"])
            cat.attributes = [attrs[c] for c in CATEGORY_ATTRS[slug]]
            cats[slug] = (cat, color)
        mans = {}
        for i, name in enumerate(MANUFACTURERS):
            mans[name], _ = await get_or_create(
                s, Manufacturer, {"name": name, "sort": (i + 1) * 10}, slug=slugify(name)
            )
        await get_or_create(s, PricingSettings, {}, id=1)
        for i, (name, price, desc) in enumerate(
            [
                ("Доставка техники на объект", 15000, "Перевозка тралом в пределах 100 км"),
                ("Услуги машиниста", 5000, "За смену"),
                ("Работа в ночную смену", 7000, "Надбавка за смену"),
            ]
        ):
            await get_or_create(
                s, ExtraService, {"price": Decimal(price), "description": desc, "sort": (i + 1) * 10}, name=name
            )

        # техника
        cat_slugs = [c[1] for c in CATEGORIES]
        for n in range(1, 51):
            ext = f"DEMO-{n:04d}"
            slug_cat = cat_slugs[(n - 1) % len(cat_slugs)]
            cat, color = cats[slug_cat]
            man = MANUFACTURERS[(n * 7) % len(MANUFACTURERS)]
            model = MODELS[(n * 3) % len(MODELS)] + ("-" + str(n % 9 + 1) if n % 4 == 0 else "")
            name = f"{SINGULAR[slug_cat]} {man} {model}"
            eq, created = await get_or_create(
                s,
                Equipment,
                {
                    "name": name,
                    "slug": slugify(f"{name}-{n}"),
                    "category_id": cat.id,
                    "manufacturer_id": mans[man].id,
                    "model": model,
                    "year": random.randint(2012, 2024),
                    "status_id": statuses[random.choice(["available", "available", "busy", "on_request"])].id,
                    "short_description": fake.sentence(nb_words=12),
                    "description": "<p>" + "</p><p>".join(fake.paragraphs(nb=3)) + "</p>",
                    "terms": "<ul><li>Минимальный срок аренды — 1 смена (8 часов)</li><li>Доставка на объект рассчитывается отдельно</li><li>Топливо — за счёт арендатора, если не оговорено иное</li></ul>",
                    "is_featured": n <= 8,
                    "price_hidden": n % 10 == 0,
                    "sort": n,
                    "meta_title": f"{name} — аренда в Дортех",
                    "meta_description": f"Аренда {name.lower()}: тарифы за смену и сутки, характеристики, заявка онлайн.",
                },
                external_id=ext,
            )
            if not created:
                continue
            shift = Decimal(random.randrange(8000, 60000, 500))
            s.add(
                Tariff(
                    equipment_id=eq.id,
                    price_per_shift=shift,
                    price_per_day=(shift * Decimal("2.4")).quantize(Decimal("1")),
                    shift_hours=8,
                    min_units=1,
                )
            )
            for k in range(2):
                fname = f"{eq.slug}-{k + 1}.jpg"
                size = placeholder(public / "equipment" / fname, f"{man} {model}", color)
                s.add(
                    EquipmentImage(
                        equipment_id=eq.id,
                        file=file_record(f"equipment/{fname}", fname, "image/jpeg", size),
                        alt=name,
                        sort=k * 10,
                    )
                )
            for code in CATEGORY_ATTRS[slug_cat]:
                a = attrs[code]
                av = AttributeValue(equipment_id=eq.id, attribute_id=a.id)
                if a.type == AttributeType.number:
                    rng = {
                        "weight": (1.5, 50),
                        "engine_power": (60, 600),
                        "bucket_volume": (0.3, 4.5),
                        "lifting_capacity": (3, 100),
                        "boom_length": (8, 60),
                    }[code]
                    av.value_number = Decimal(str(round(random.uniform(*rng), 1)))
                elif a.type == AttributeType.choice:
                    av.option_id = options[(code, random.choice(ATTR_OPTIONS[code]))].id
                elif a.type == AttributeType.bool:
                    av.value_bool = random.random() < 0.7
                s.add(av)
        await s.flush()

        # контент
        for i, (title, desc) in enumerate(
            [
                ("Аренда спецтехники с экипажем", "Опытные машинисты, допуски и страхование"),
                ("Аренда без экипажа", "Техника в исправном состоянии под ваш персонал"),
                ("Земляные работы", "Разработка котлованов и траншей"),
                ("Перевозка сыпучих грузов", "Самосвалы 10–40 т"),
                ("Доставка техники тралом", "Низкорамные тралы до 60 т"),
                ("Планировка и уплотнение", "Бульдозеры, грейдеры, катки"),
                ("Демонтаж", "Экскаваторы с гидромолотом"),
                ("Подъём грузов", "Автокраны 16–100 т"),
                ("Благоустройство", "Мини-техника для городских объектов"),
                ("Зимнее содержание", "Уборка и вывоз снега"),
            ]
        ):
            svc, created = await get_or_create(
                s,
                Service,
                {
                    "title": title,
                    "short_description": desc,
                    "body": "<p>" + "</p><p>".join(fake.paragraphs(nb=3)) + "</p>",
                    "sort": (i + 1) * 10,
                },
                slug=slugify(title),
            )
            if created:
                size = placeholder(public / "services" / f"{svc.slug}.jpg", title, "#374151", (900, 600))
                svc.cover = file_record(f"services/{svc.slug}.jpg", f"{svc.slug}.jpg", "image/jpeg", size)
        for i in range(10):
            title = f"{random.choice(['Строительство', 'Реконструкция', 'Ремонт', 'Благоустройство'])} {random.choice(['дороги', 'развязки', 'котлована', 'набережной', 'промплощадки', 'моста'])} — {fake.city()}"
            prj, created = await get_or_create(
                s,
                Project,
                {
                    "title": title,
                    "year": 2024 - i % 4,
                    "customer_name": fake.company(),
                    "location": fake.city(),
                    "short_description": fake.sentence(nb_words=14),
                    "body": "<p>" + "</p><p>".join(fake.paragraphs(nb=3)) + "</p>",
                    "sort": (i + 1) * 10,
                },
                slug=slugify(f"{title}-{i + 1}"),
            )
            if created:
                size = placeholder(public / "projects" / f"{prj.slug}.jpg", f"Проект {i + 1}", "#1f2937", (900, 600))
                prj.cover = file_record(f"projects/{prj.slug}.jpg", f"{prj.slug}.jpg", "image/jpeg", size)
        for i in range(10):
            title = f"{random.choice(['Новая техника в парке', 'Как выбрать', 'Сезон', 'Отчёт', 'Советы'])}: {fake.sentence(nb_words=5).rstrip('.')}"
            pub, created = await get_or_create(
                s,
                Publication,
                {
                    "title": title,
                    "short_description": fake.sentence(nb_words=16),
                    "body": "<p>" + "</p><p>".join(fake.paragraphs(nb=4)) + "</p>",
                    "published_at": datetime.now(UTC) - timedelta(days=i * 9),
                },
                slug=slugify(f"{title}-{i + 1}"),
            )
            if created:
                size = placeholder(
                    public / "publications" / f"{pub.slug}.jpg", f"Публикация {i + 1}", "#0f172a", (900, 600)
                )
                pub.cover = file_record(f"publications/{pub.slug}.jpg", f"{pub.slug}.jpg", "image/jpeg", size)
        await get_or_create(
            s,
            Page,
            {
                "title": "О компании",
                "body": "<p>ООО «ДОРТЕХ» — аренда дорожно-строительной техники. "
                + " ".join(fake.paragraphs(nb=3))
                + "</p>",
                "sort": 10,
            },
            slug="about",
        )
        await get_or_create(
            s,
            Page,
            {
                "title": "Политика обработки персональных данных",
                "body": "<p>Настоящая политика определяет порядок обработки персональных данных пользователей сайта в соответствии с Федеральным законом от 27.07.2006 № 152-ФЗ «О персональных данных».</p><p>Текст предоставляется Заказчиком.</p>",
                "show_in_footer": True,
                "sort": 20,
            },
            slug="privacy",
        )
        await get_or_create(
            s,
            Page,
            {
                "title": "Пользовательское соглашение",
                "body": "<p>Текст предоставляется Заказчиком.</p>",
                "show_in_footer": True,
                "sort": 30,
            },
            slug="terms",
        )
        ss, created = await get_or_create(
            s,
            SiteSettings,
            {
                "phone": "+7 (846) 000-00-00",
                "email": "info@dortech.example",
                "address": "г. Самара, ул. Примерная, 1",
                "working_hours": "Пн–Пт 8:00–18:00",
                "hero_title": "Аренда спецтехники для дорожного и промышленного строительства",
                "hero_subtitle": "Экскаваторы, погрузчики, автокраны, самосвалы и катки — с экипажем и без. Расчёт стоимости онлайн.",
                "about_short": "Более 15 лет обеспечиваем строительные объекты надёжной техникой и опытными машинистами.",
                "stats": [
                    {"value": "15+", "label": "лет на рынке"},
                    {"value": "120", "label": "единиц техники"},
                    {"value": "400+", "label": "выполненных проектов"},
                ],
                "footer_text": "© ООО «ДОРТЕХ»",
                "default_meta_title": "Дортех — аренда спецтехники",
                "default_meta_description": "Аренда спецтехники с экипажем и без: экскаваторы, погрузчики, автокраны, самосвалы. Онлайн-заявка и предварительный расчёт.",
            },
            id=1,
        )

        # пользователи и организации
        org_a, _ = await get_or_create(
            s,
            Organization,
            {
                "inn": "6316123456",
                "kpp": "631601001",
                "phone": "+7 (846) 111-11-11",
                "email": "office@stroyalliance.example",
            },
            name="ООО «СтройАльянс»",
        )
        org_b, _ = await get_or_create(
            s,
            Organization,
            {"inn": "6318654321", "kpp": "631801001", "phone": "+7 (846) 222-22-22", "email": "office@dormost.example"},
            name="ООО «ДорМост»",
        )
        users = {}
        for email, role, org, ln, fn in [
            ("admin@dortech-demo.ru", Role.admin, None, "Администратор", "Сайта"),
            ("manager@dortech-demo.ru", Role.manager, None, "Петров", "Иван"),
            ("client-a@dortech-demo.ru", Role.client, org_a, "Сидоров", "Алексей"),
            ("client-b@dortech-demo.ru", Role.client, org_b, "Кузнецова", "Мария"),
        ]:
            users[email], _ = await get_or_create(
                s,
                User,
                {
                    "password_hash": hash_password(PASSWORD),
                    "last_name": ln,
                    "first_name": fn,
                    "role": role,
                    "organization_id": org.id if org else None,
                    "email_confirmed_at": datetime.now(UTC),
                    "phone": fake.phone_number(),
                },
                email=email,
            )
        await s.commit()

        # заявки
        existing = (await s.execute(select(Inquiry.id))).scalars().first()
        if existing is None:
            eq_ids = (await s.execute(select(Equipment.id).where(Equipment.is_published.is_(True)))).scalars().all()
            for i in range(15):
                user = (
                    users["client-a@dortech-demo.ru"]
                    if i % 3 == 0
                    else (users["client-b@dortech-demo.ru"] if i % 3 == 1 else None)
                )
                if user is not None:
                    await s.refresh(user, ["organization"])
                start = date.today() + timedelta(days=random.randint(3, 30))
                data = InquiryCreateIn(
                    items=[
                        EstimateItemIn(
                            equipment_id=random.choice(eq_ids),
                            quantity=random.randint(1, 2),
                            unit=random.choice(["shift", "day"]),
                        )
                        for _ in range(random.randint(1, 3))
                    ],
                    period_from=start,
                    period_to=start + timedelta(days=random.randint(1, 20)),
                    extra_service_ids=[1] if i % 2 else [],
                    contact_name=str(user) if user else fake.name(),
                    contact_phone=fake.phone_number(),
                    contact_email=user.email if user else fake.email(),
                    company_name=None,
                    work_place=f"{fake.city()}, {fake.street_address()}",
                    comment=fake.sentence() if i % 2 else None,
                    consent=True,
                )
                await create_inquiry(s, data, user=user, source=InquirySource.account if user else InquirySource.web)
            await s.commit()
        print("seed ok")


if __name__ == "__main__":
    asyncio.run(seed())
