# План работ: сайт ООО «ДОРТЕХ»

Соглашение №ДТ-261026 от 26.10.2026, Приложения 1–3 (`03_Спецификация_ТЗ_и_график.docx`).
Исполнитель: ИП Росавский А.А. Срок: 27.10 – 16.11.2026, проверка Заказчиком 17–23.11.2026.


---

## 1. Контекст

- Нужен корпоративный сайт аренды спецтехники: публичные разделы, каталог с фильтрами и сравнением, заявка с предварительным расчётом по тарифам, кабинет клиента, кабинет менеджера, панель администратора, CSV импорт/экспорт, email, webhook. 1С, CRM, эквайринг, ЭП, SMS — вне объёма (ТЗ 5.2).
- В текущем репозитории лежит прототип **другого** проекта («СамараДорСнаб», запчасти под 1С-Битрикс): 6 статических HTML, SCSS, vanilla JS, Webpack. Бэкенда, картинок и git-remote нет; JS местами не совпадает с HTML. Документация в корне (TZ.md, ROADMAP.md, README.md, 1C_INTEGRATION.md) описывает Битрикс/1С и к Дортех не относится.
- Переиспользуем только дизайн-токены и миксины из `project/src/scss/_variables.scss` и `_mixins.scss`, а также алгоритмы проверки ИНН/КПП и маску телефона из `project/src/js/components/form-validator.js` (портируем в TypeScript). Всё остальное — заново.
- Локальная среда: macOS, Node 26, Python 3.12 + uv. Docker и PostgreSQL не установлены.

## 2. Принятые решения (согласованы с пользователем)

| Вопрос | Решение |
|---|---|
| Стек | **FastAPI + SQLAlchemy 2 (async, asyncpg) + Alembic + PostgreSQL 16**; фронт **Next.js (App Router, React 19, TypeScript, Sass)**. Соответствует ТЗ 5.3 (React + Python + PostgreSQL) |
| Панель администратора | **starlette-admin 1.0.x** (монтируется в FastAPI; async SQLAlchemy, русский интерфейс, TinyMCE, хуки CRUD, импорт CSV с предпросмотром, файловое хранилище) |
| Кабинет менеджера и клиента | Кастомные страницы Next.js поверх REST API |
| Репозиторий | **Новый отдельный репозиторий** `dortech` (предлагаемый путь `/Users/rosavskii/projects/dortech`). Этот репозиторий не трогаем, кроме сохранения `PLAN.md` |
| Хостинг | Тестовая среда — VPS Исполнителя с 27–28.10; прод — сервер Заказчика (4 vCPU / 8 ГБ / SSD, Ubuntu 24.04). Если доступы к серверу Заказчика задерживаются, прод временно на VPS Исполнителя, задержка фиксируется письменно (Прил. 3 п. 2) |
| Аутентификация | Серверные сессии: таблица `sessions`, HttpOnly Secure cookie, CSRF double-submit (`X-CSRF-Token`). Блокировка пользователя завершает его сессии немедленно (ТЗ 4.3) |
| Прокси и HTTPS | **Caddy** (автоматический Let's Encrypt, HSTS). Приватные файлы отдаёт FastAPI `FileResponse` после проверки прав; файлы ≤20 МБ, этого достаточно |
| Фоновые задачи | Без Celery/Redis: таблица `outbox` + процесс `python -m app.worker` (email, webhook, повторы) |
| Поиск | PostgreSQL `pg_trgm` по названию и модели; фильтры по EAV-характеристикам с индексами |
| Контейнеры локально | **OrbStack** (тот же `docker compose`, что на VPS) |

## 3. Структура нового репозитория

```
dortech/
├── backend/            FastAPI
│   ├── app/
│   │   ├── core/       settings, db, security, deps, pagination, errors
│   │   ├── models/     SQLAlchemy-модели по доменам
│   │   ├── schemas/    Pydantic v2
│   │   ├── api/        routers: public/, account/, manager/, auth/, files/
│   │   ├── services/   pricing, inquiries, csv_import, outbox, audit, search
│   │   ├── admin/      starlette-admin: views, auth provider, custom views
│   │   ├── worker.py   цикл outbox
│   │   └── main.py
│   ├── alembic/        миграции
│   ├── scripts/        seed_demo.py, gen_import_csv.py, import_catalog.py
│   ├── tests/          pytest + httpx
│   └── pyproject.toml  (uv)
├── frontend/           Next.js (App Router, TS, Sass modules, TanStack Query)
│   ├── src/app/ src/components/ src/lib/ src/styles/(_tokens.scss, _mixins.scss)
│   └── e2e/            Playwright (360/768/1440)
├── deploy/             docker-compose.dev.yml, docker-compose.yml, docker-compose.edge.yml,
│                       Caddyfile, .env.example, deploy.sh, backup.sh, restore.sh, cron/
├── load/               k6: catalog.js
├── docs/               PLAN.md, ARCHITECTURE.md, API.md, WEBHOOK.md, CSV_TEMPLATE.md,
│                       INSTALL.md, RESTORE.md, OPERATIONS.md, ADMIN_MANUAL.md,
│                       DB_SCHEMA.md, LICENSES.md, ACCESS_HANDOVER.md, DEMO_AGENDA.md,
│                       protocols/
├── Makefile            up / migrate / seed / test / e2e / lint / load
└── README.md
```

## 4. Модель данных (ключевые таблицы)

| Таблица | Поля и связи |
|---|---|
| `users` | email (unique), password_hash (argon2), ФИО, phone, position, `role` ∈ {client, manager, admin}, organization_id (null для сотрудников), is_active, blocked_at, blocked_reason, email_confirmed_at |
| `sessions` | id (opaque token hash), user_id, created_at, expires_at, ip, user_agent |
| `email_tokens` | user_id, kind ∈ {confirm, reset}, token_hash, expires_at, used_at |
| `organizations` | name, inn, kpp, legal_address, phone, email, note |
| `categories` | parent_id (≤2 уровня), name, slug, image, sort, is_featured, + SEO |
| `manufacturers` | name, slug, logo |
| `availability_statuses` | code, name, color, allow_request (словарь, редактирует админ) |
| `attribute_definitions` | code, name, unit, type ∈ {number, string, bool, choice}, is_filterable, is_comparable, sort; M2M с категориями |
| `attribute_options` | attribute_id, value, sort |
| `attribute_values` | equipment_id, attribute_id, value_number / value_text / value_bool / option_id; unique(equipment, attribute) |
| `equipment` | external_id (unique, null), name, slug, category_id, manufacturer_id, model, year, short_description, description (HTML), terms (HTML), status_id, is_published, is_featured, price_hidden, sort, + SEO; GIN pg_trgm(name, model) |
| `equipment_images` | equipment_id, file, alt, sort |
| `tariffs` | equipment_id (1:1), price_per_shift, price_per_day, shift_hours=8, min_units=1, note |
| `extra_services` | name, price (фикс. за заявку), is_active, sort |
| `pricing_settings` | singleton: rounding_step ∈ {1,10,100}, vat_label, disclaimer_text |
| `inquiries` | public_id (UUID), number `DT-000123`, organization_id (null для гостя), created_by, contact_name/phone/email, company_name_raw, period_from/to, work_place, comment, status ∈ {new, clarification, offer_sent, agreed, completed, cancelled}, assigned_to, estimated_total, estimate_snapshot (JSON), source ∈ {web, account, repeat}, parent_id |
| `inquiry_items` | inquiry_id, equipment_id (RESTRICT), name/model snapshot, quantity, units, unit ∈ {shift, day}, unit_price_snapshot, line_total (null → «по запросу») |
| `inquiry_extra_services` | inquiry_id, service_id, name/price snapshot |
| `inquiry_status_history` | inquiry_id, from_status, to_status, changed_by, comment, created_at |
| `inquiry_comments` | inquiry_id, author_id, text, is_internal |
| `attachments` | public_id, inquiry_id, organization_id (денормализация для изоляции), uploaded_by, path (имя = UUID, вне веб-корня), original_name, content_type, size, kind ∈ {client_doc, offer_pdf} |
| `contact_messages` | name, phone, email, text |
| `pages`, `services`, `projects`, `publications` | slug, title, body (HTML, TinyMCE), cover, is_published, sort / published_at, + SEO; `projects`: year, customer_name, images |
| `site_settings` | singleton: контакты, режим работы, карта, hero, notification_emails |
| `redirects` | old_path (unique), new_path, status ∈ {301, 302}, is_active |
| `import_jobs` | file, dry_run, status, counts (total/created/updated/failed), report_file, started_by |
| `webhook_endpoints` | url, secret, is_active, events |
| `outbox` | kind ∈ {email, webhook}, endpoint_id, payload (JSON), status, attempts, next_attempt_at, last_error, response_code |
| `audit_log` | actor_id, action, target_type, target_id, object_repr, changes (JSON), ip, created_at |

SEO-поля (миксин): meta_title, meta_description, og_image, noindex.

## 5. REST API `/api/v1/` и изоляция данных

- **Публичные** (только чтение, `is_published=True`, throttle по IP): категории, производители, статусы, фасеты; `GET equipment/?q&category&manufacturer&status&attr_<code>=&attr_<code>_min/_max&ordering&page`; `GET equipment/{slug}`; `GET compare/?ids=` (≤4, 5 → 400); контент (home, settings, pages, services, projects, publications, redirects, sitemap); `POST inquiries/estimate/`; `POST inquiries/` (10/ч на IP, honeypot; ответ `{public_id, number, estimate}`); `POST contact-messages/`; `auth/` (csrf, register, confirm-email, login, logout, password-reset, password-reset/confirm, me).
- **Клиент** (`role=client`): профиль организации; свои заявки, комментарии (без `is_internal`), файлы. Повтор заявки — фронт собирает корзину из детали и шлёт `POST inquiries/` с `parent`.
- **Менеджер** (`role ∈ {manager, admin}`): список заявок с фильтрами (status, assigned_to, organization, dates, q), деталь, назначение, смена статуса, комментарии, загрузка PDF-предложения, `export.csv`, организации, список менеджеров. Менеджеры видят все заявки, назначение = ответственность (подтвердить у Заказчика 27.10).
- **Администратор**: starlette-admin (HTML), отдельного REST не нужно.
- **Изоляция** (критерий приёмки «Разделение доступа»): одна зависимость `current_organization`, все клиентские запросы фильтруются по `organization_id`; объекты адресуются UUID, чужой объект → 404; файлы отдаются только через `GET files/{uuid}/download/` после проверки (организация владельца или сотрудник), прямых URL на приватные файлы нет. Автотест `test_tenant_isolation.py` параметризован списком всех клиентских маршрутов и падает, если новый маршрут не внесён в список.
- Загрузка файлов: ≤20 МБ (Caddy `request_body` + проверка в API), белый список pdf/doc/docx/xls/xlsx/jpg/png по расширению и magic-байтам, имя заменяется на UUID.

## 6. Предварительный расчёт (ТЗ 3.2, только сервер)

Вход: позиции `{equipment, quantity, units, unit ∈ {shift, day}}`, период, доп. услуги. `units` по умолчанию = календарные дни периода включительно.
`line = unit_price × max(units, min_units) × quantity`; без тарифа или при `price_hidden` → `line = null`, `needs_quote = true`. Округление каждой строки `ROUND_HALF_UP` до `rounding_step` (Decimal). `total = Σ line + Σ extra.price`; `is_partial = any(needs_quote)`.
Фронт показывает блок «Предварительный расчёт, не является офертой» с `disclaimer_text` и `vat_label`; при `is_partial` — «от N ₽ + позиции по запросу». При создании заявки расчёт пересчитывается и сохраняется в `estimate_snapshot`. Формула и округление фиксируются в `docs/ARCHITECTURE.md` и согласуются 27–28.10.

## 7. Обмен данными

- **Webhook** `inquiry.created`: `POST url`, заголовки `X-Dortech-Event`, `X-Dortech-Delivery` (UUID), `X-Dortech-Timestamp`, `X-Dortech-Signature: sha256=HMAC-SHA256(secret, timestamp + "." + body)`. Тело: number, status, source, organization, contact, period, work_place, items (с external_id и ценами), extra_services, estimate, links. Запись в `outbox` в одной транзакции с заявкой; воркер шлёт через httpx (таймаут 10 с), повторы 1 мин → 5 мин → 30 мин → 2 ч → 12 ч → 24 ч, затем `failed`; переотправка из админки. Документ `docs/WEBHOOK.md` с примером проверки подписи на Python. Приёмник для теста — встроенный `webhook_sink` (включается переменной окружения, виден в админке).
- **CSV-импорт каталога**: UTF-8 с BOM, разделитель `;`. Колонки: `external_id*; name*; slug; category* (slug); manufacturer; model; year; status; short_description; description; terms; price_per_shift; price_per_day; shift_hours; min_units; price_hidden; is_published; images (через |); meta_title; meta_description; attr:<code>…`. Upsert по `external_id`, дубль в файле → последняя строка + предупреждение, неизвестная категория → ошибка строки, производитель создаётся по имени. Сначала валидация всех строк, затем запись пачками по 200 в транзакции. Синхронно: 1 000 строк ≈ секунды. Запуск: страница в админке (dry-run + отчёт `errors.csv` со строкой/полем/сообщением) и CLI `scripts/import_catalog.py`. `scripts/gen_import_csv.py --rows 1000 --duplicates 50 --invalid 20` для приёмки.
- **Экспорт заявок** CSV (менеджер, с фильтрами), проверяется открытием в Excel.
- **Email** через SMTP Заказчика (aiosmtplib + Jinja2), 5 шаблонов: подтверждение email, сброс пароля, новая заявка клиенту, новая заявка менеджерам, смена статуса. В dev/test — Mailpit.

## 8. Маршруты Next.js

| Маршрут | Рендер |
|---|---|
| `/`, `/about`, `/services[/[slug]]`, `/projects[/[slug]]`, `/publications[/[slug]]`, `/contacts` | SSR, `revalidate: 60`, клиентские островки для форм |
| `/catalog[/[category]]` (фильтры в searchParams) | SSR `no-store`; фильтры и сортировка — клиентский островок с URL-state |
| `/equipment/[slug]` | SSR `revalidate: 60`; галерея, «в заявку», «сравнить» — клиент |
| `/compare`, `/request`, `/request/success` | клиент; корзина заявки и ids сравнения в localStorage |
| `/[...slug]` | SSR: страница по slug → иначе редирект из `redirects` → иначе 404 |
| `/login`, `/register`, `/register/confirm`, `/password-reset[/confirm]` | клиент |
| `/account/*` (заявки, деталь, профиль), `/manager/*` (заявки, деталь, организации) | layout — серверная проверка сессии (`GET auth/me` с пробросом cookie, `no-store`), страницы — TanStack Query; `noindex` |
| `sitemap.ts`, `robots.ts`, `middleware.ts` | sitemap из API, robots по `ROBOTS_ALLOW`, middleware только редиректит на `/login?next=` без cookie |

В dev `/api` проксируется `rewrites` на `:8000`; в prod — Caddy, один домен, CORS не нужен. Токены Sass портируются из `project/src/scss/` на `@use`, `math.div`, `color.adjust`; breakpoints 360 / 768 / 1440 (ТЗ 2.4). Брендовые цвета заменяются после получения материалов Заказчика.

## 9. Инфраструктура

- **Локально**: OrbStack; `deploy/docker-compose.dev.yml` → `postgres:16`, `mailpit`. Бэкенд и фронт нативно: `uv run uvicorn app.main:app --reload`, `npm run dev`. `make seed` → `scripts/seed_demo.py` (Faker ru_RU, идемпотентно по external_id): 8 категорий, 12 производителей, 50 карточек с характеристиками и плейсхолдерами, 10 услуг, 10 проектов, 10 публикаций, тарифы, пользователи `admin / manager / client_a / client_b` (две организации), 15 заявок с историей.
- **VPS (test у Исполнителя, prod у Заказчика)**: Ubuntu 24.04, Docker Engine + compose. Каталог `/srv/dortech/<env>/` → `src/`, `.env` (600), `media/`, `logs/`, `backups/`. Сервисы: `postgres`, `backend` (uvicorn, 4 воркера), `worker`, `frontend` (Next standalone), `caddy` (edge, 80/443). Маршрутизация: `/api/*`, `/admin/*` (путь из `ADMIN_URL_PATH`) → backend; `/media/public/*` → file_server; остальное → frontend. Приватные файлы наружу не выдаются.
- **`.env.example`**: SECRET_KEY, DATABASE_URL, ALLOWED_HOSTS, SITE_URL, ADMIN_URL_PATH, SMTP_*, DEFAULT_FROM_EMAIL, WEBHOOK_URL, WEBHOOK_SECRET, WEBHOOK_SINK_ENABLED, INTERNAL_API_URL, NEXT_PUBLIC_SITE_URL, ROBOTS_ALLOW, SENTRY_DSN (пусто), BACKUP_RETENTION_DAYS.
- **Деплой** `deploy/deploy.sh <env> <git-ref>`: fetch/checkout → build → `alembic upgrade head` → `up -d` → `curl /api/health` (отдаёт `{version, commit}` — реквизит протоколов по ТЗ 6.1). Prod принимает только теги `vX.Y.Z`. Test: basic-auth в Caddy, `noindex`, SMTP = Mailpit.
- **Бэкапы**: host cron 03:00 → `backup.sh`: `pg_dump -Fc` + sha256 + `counts.json` (строки ключевых таблиц) + еженедельный tar `media/`; ретенция 14 дневных / 8 недельных; внешняя копия через rclone, если Заказчик даст хранилище. **Учебное восстановление** `restore.sh`: стоп, dropdb/createdb, pg_restore, `alembic check`, сверка counts, вход клиентом и менеджером; лог через `tee` в `docs/protocols/restore-drill-<дата>.log` + md-протокол.
- **Логи**: uvicorn/app → stdout (json-file, ротация 20 МБ × 5) + `logs/app-error.log` (WARNING+, RotatingFileHandler); Caddy access-log с ротацией; Sentry подключается непустым DSN (опционально).
- **Безопасность к передаче**: HTTPS + HSTS; Secure/HttpOnly/SameSite=Lax cookie; CSRF; rate limit (slowapi) на вход/регистрацию/восстановление/публичные формы; валидация загрузок; CORS закрыт; нестандартный путь админки; `uv.lock` + `package-lock.json`; `pip-audit` / `npm audit` в CI; страница политики ПДн (152-ФЗ) и чекбокс согласия; блокировка пользователя; DEBUG выключен, секреты только в `.env`.

## 10. Проверки под таблицу приёмки (ТЗ 6)

Инструменты: pytest + httpx (против PostgreSQL из compose, отдельная test-БД), Playwright (три проекта 360/768/1440, проверка `scrollWidth <= innerWidth`), k6. CI — GitHub Actions на push и теге.

| Проверка ТЗ | Автоматически | Вручную в протоколе |
|---|---|---|
| Публичные страницы | Playwright обходит URL из sitemap: 200, h1, нет горизонтальной прокрутки, меню/формы кликабельны | Правка текста в админке → страница обновилась; скриншоты |
| Каталог | Контрольный набор `tests/fixtures/control_set.json` (20 карточек): поиск по названию/модели, каждый фильтр, комбинации, сортировка, пагинация, `?page=abc` и пустой запрос → 200; сравнение 4 → 200, 5 → 400 | Таблица «запрос → ожидаемые карточки» |
| Заявка | POST гостем и клиентом → номер, запись в БД, история статусов, outbox email + webhook; GET менеджером и владельцем 200; Playwright полный сценарий на 360 | Проверка в кабинете менеджера |
| Разделение доступа | `test_tenant_isolation.py`: логин A, объекты B → 403/404, списки без чужих id, файл B → 404, аноним → 401 | Подстановка чужих id в адресную строку, скриншоты |
| Обмен данными | `test_import.py`; `gen_import_csv` 1 000 строк → импорт → отчёт; повторный импорт даёт 0 новых; `webhook_sink` принял и HMAC верна; email в Mailpit | Один реальный email через SMTP Заказчика; экспорт CSV в Excel |
| Нагрузка | k6 `load/catalog.js`: 50 VU, 1 мин разгон + 10 мин; список, поиск, фильтр, карточка, категории, пауза 1–3 с; пороги `http_req_failed<0.01`, `p(95)<2000`; `--summary-export` | `docs/protocols/load-<дата>.md`: nproc, free -h, ОС/Docker, `/api/health` (тег + commit), параметры uvicorn, JSON k6 |
| Резервная копия | `restore.sh` + сверка counts | Протокол восстановления |
| Код и эксплуатация | CI зелёный на теге; `deploy.sh` в чистый каталог по `INSTALL.md` | `docs/protocols/defects.md` с классификацией по ТЗ 6.2 |

## 11. Комплект передачи (ТЗ 7)

Рабочая версия на домене Заказчика и `test.<domain>`; тег `v1.0.0` + `git archive` zip; `alembic/` + `docs/DB_SCHEMA.md` (ERD, таблицы, индексы); `INSTALL.md`, `RESTORE.md`, `OPERATIONS.md`; `ADMIN_MANUAL.md`; `LICENSES.md` (`pip-licenses` + `license-checker`); `protocols/TEST_PROTOCOL_v1.0.0.md` (реквизиты, таблица по строкам ТЗ 6, сводка pytest/Playwright, нагрузка, восстановление, дефекты, подписи) + `load-*.md`, `restore-drill-*.md`, `defects.md`; `ACCESS_HANDOVER.md` (перечень без значений; значения — защищённым каналом); `DEMO_AGENDA.md` (≤2 ч: архитектура, публичный сайт и контент, каталог, заявка и расчёт, кабинет клиента, менеджер и админка, обмен, эксплуатация, вопросы).

## 12. Календарь (Прил. 3) и план по дням

| Дата | Результат дня |
|---|---|
| **27.10 пн** | Чек-лист материалов Заказчику (раздел 14). `docs/ARCHITECTURE.md`: карта страниц, ER, 3 сценария, статусы, формула расчёта, CSV-шаблон, JSON webhook — на согласование. Новый репозиторий: каркас backend (FastAPI, SQLAlchemy async, Alembic, settings, `/api/health`), frontend (Next.js, порт токенов Sass), deploy (compose dev/prod, Caddyfile, `.env.example`), Makefile, CI. Модели и первая миграция: users, organizations, catalog, pricing, content, inquiries. starlette-admin с auth provider и ru-локалью. `seed_demo.py`. Вечером: VPS Исполнителя — Docker, Caddy, DNS `test.`, первый деплой |
| **28.10 вт** | **Демонстрационный прототип на тестовом URL**: главная, каталог с реальными поиском и фильтрами из API, карточка техники, корзина заявки → форма → номер в БД, заявка и каталог видны в админке; страница UI-kit; статичные макеты `/account` и `/manager` на мок-данных; проверка 360/768/1440; список вопросов Заказчику (ответ ≤2 р.д.) |
| 29.10 ср | Каталог backend: EAV-фильтры, фасеты, trgm-поиск, сортировка, пагинация, сравнение, тесты пустых и некорректных запросов; загрузка изображений в админке |
| 30.10 чт | Каталог UI: фильтры (шторка на мобильном), чипсы, URL-state, карточка (галерея, характеристики, тариф или «запросить предложение»), сравнение до 4 |
| 31.10 пт | Контент: TinyMCE в админке, SEO-поля, редиректы, настройки сайта; главная, о компании, услуги, проекты, публикации, контакты, служебные страницы; catch-all, sitemap/robots/metadata; начало наполнения |
| 01.11 сб | Адаптивный проход публичных страниц; форма контактов; резерв |
| 02.11 вс | Резерв: наполнение, Lighthouse и SEO-проверка |
| **03.11 пн** | **Демо «Публичный сайт и каталог»**, сбор замечаний. Backend auth: регистрация, подтверждение, вход, выход, сброс; сессии, CSRF; письма через outbox + Mailpit |
| 04.11 вт | Праздник, в календаре ТЗ отсутствует — резерв на замечания |
| 05.11 ср | Страницы auth в Next, middleware, серверная проверка сессии, layout `/account`; профиль организации (API + UI) |
| 06.11 чт | Заявки: статус-машина, история, комментарии, назначение, сервис `estimate` + тесты округления, snapshot, нумерация; `/account/inquiries` список и деталь, повтор заявки; smoke-нагрузка каталога |
| 07.11 пт | Файлы: валидация, приватное хранилище, выдача с проверкой прав; UI клиента; PDF-предложение менеджера; **suite изоляции организаций** |
| 08.11 сб | Кабинет менеджера: список с фильтрами, деталь (статус, назначение, комментарии, файлы), экспорт CSV |
| 09.11 вс | Резерв: адаптив кабинетов (таблицы → карточки на 360) |
| **10.11 пн** | Роли и блокировка (с завершением сессий), `audit_log` через хуки админки и сервисный слой (статус, назначение, роль, блокировка, тариф, удаление), подтверждения удаления, RESTRICT на связях; **демо «Кабинеты и заявки»** |
| 11.11 вт | CSV-импорт: сервис, страница в админке, dry-run, отчёт, CLI; прогон 1 000 строк с дублями; экспорт проверен в Excel |
| 12.11 ср | Webhook (подпись, воркер, повторы, переотправка, `WEBHOOK.md`); email через SMTP Заказчика; **прод на сервере Заказчика**: Docker, Caddy, DNS, HTTPS, первый деплой |
| 13.11 чт | Комплексная проверка: suite изоляции, k6 50 VU / 10 мин против прода (индексы, кэш справочников, воркеры), бэкап + учебное восстановление с записью, журнал ошибок; исправления; **заморозка функционала** |
| 14.11 сб | Документация (INSTALL, RESTORE, OPERATIONS, ADMIN_MANUAL, DB_SCHEMA, LICENSES, ACCESS_HANDOVER), протокол тестирования, контент Заказчика на проде |
| 15.11 вс | Резерв: повторный прогон CI и k6 после исправлений, вычитка, кандидат тега |
| **16.11 пн** | **Передача**: тег `v1.0.0`, деплой прода по тегу, `git archive`, документы, доступы, демонстрация ≤2 ч, письмо о передаче на приёмку |
| 17–23.11 | Проверка Заказчиком; блокирующие дефекты (ТЗ 6.2) устраняются и перепроверяются с обновлением протокола |

## 13. Риски и меры

- Материалы, тарифы, SMTP, сервер от Заказчика с опозданием → синтетические данные с 27.10; письменная фиксация задержки (Прил. 3 п. 2); прод временно на VPS Исполнителя.
- FastAPI вместо Django: auth, email, админка собираются из библиотек, а не «из коробки» → каркас и starlette-admin поднимаются в первый день, auth выделено 03–05.11; выходные — буфер.
- Утечка между организациями → одна зависимость `current_organization`, UUID, приватные файлы, suite изоляции как gate в CI с 07.11.
- p95 > 2 с → индексы, пагинация, `revalidate` публичных страниц, 4 воркера uvicorn; smoke-нагрузка 06.11, не только 13.11.
- Разрастание словаря характеристик → 4 фиксированных типа, настройка фильтров только в админке.
- Кэш SSR с сессиями → все авторизованные fetch `no-store`, `/auth/me` никогда не кэшируется.
- Один разработчик → feature-freeze 13.11, приоритет блокирующим дефектам.

## 14. Что нужно от Заказчика до 27.10 (Прил. 3 п. 2)

Перечень техники с характеристиками и статусами; изображения и тексты с правами использования; тарифы за смену/день и доп. услуги, правила округления; услуги, проекты, публикации, «о компании», контакты; логотип и фирменные цвета; рабочий домен и DNS; доступ к серверу (4 vCPU / 8 ГБ / SSD); SMTP; URL приёмника webhook (если есть); список менеджеров и администратора; решения: показывать ли цены публично, видят ли менеджеры все заявки или только назначенные.

## 15. Как проверяем результат

- Каждая контрольная точка календаря демонстрируется на тестовом URL (28.10, 03.11, 10.11) и фиксируется списком замечаний.
- Каждая строка таблицы ТЗ 6 закрыта автотестом или пунктом протокола (раздел 10); CI зелёный на теге `v1.0.0`.
- Учебное восстановление из бэкапа и нагрузочный прогон записаны с конфигурацией сервера, версией кода и сценарием (ТЗ 6.1).
- Чистая установка по `INSTALL.md` в пустой каталог на тестовом VPS перед передачей.
