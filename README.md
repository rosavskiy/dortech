# Дортех — корпоративный сайт

Сайт ООО «ДОРТЕХ»: каталог спецтехники, заявки с предварительным расчётом, кабинеты клиента и менеджера, панель администратора.

- `backend/` — FastAPI + SQLAlchemy (async) + Alembic + PostgreSQL 16, панель администратора starlette-admin
- `frontend/` — Next.js (App Router, TypeScript, Sass)
- `deploy/` — docker compose, Caddy, скрипты деплоя и резервного копирования
- `load/` — сценарии нагрузочного тестирования k6
- `docs/` — план работ, архитектура, инструкции, протоколы

Быстрый старт: см. `docs/INSTALL.md` (локальная разработка — `make up && make migrate && make seed`).
