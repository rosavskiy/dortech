# Установка и развёртывание

## 1. Локальная разработка (macOS / Linux)

Требования: Python 3.12 + [uv](https://docs.astral.sh/uv/), Node.js 22+, PostgreSQL 16 (локально или Docker), Mailpit (для писем).

```bash
git clone git@github.com:rosavskiy/dortech.git && cd dortech
# БД: либо docker compose -f deploy/docker-compose.dev.yml up -d (PostgreSQL + Mailpit),
# либо локальный PostgreSQL: createuser dortech -P; createdb -O dortech dortech; createdb -O dortech dortech_test
cd backend && uv sync && uv run alembic upgrade head && uv run python -m scripts.seed_demo && cd ..
cd frontend && npm ci && cd ..
```

Запуск (три терминала или `make backend`, `make frontend`, `make worker`):

```bash
cd backend && uv run uvicorn app.main:app --reload --port 8000   # API + панель /admin
cd backend && uv run python -m app.worker                         # отправка писем и webhook
cd frontend && npm run dev                                        # сайт http://localhost:3000
```

Переменные окружения бэкенда читаются из `backend/.env` (см. `deploy/.env.example`); для разработки значения по умолчанию уже рабочие (`DATABASE_URL`, SMTP на Mailpit `localhost:1025`). Для локальных прогонов e2e удобно задать `RATE_LIMIT_ENABLED=0` и `WEBHOOK_SINK_ENABLED=1` с `WEBHOOK_URL=http://127.0.0.1:8000/api/v1/webhook-sink`, `WEBHOOK_SECRET=dev-secret`. Панель: http://localhost:8000/admin. Демо-пользователи: `admin@dortech-demo.ru`, `manager@dortech-demo.ru`, `client-a@dortech-demo.ru`, `client-b@dortech-demo.ru`, пароль `Dortech2026!`.

Проверки: `make test` (pytest, нужна БД `dortech_test`), `make e2e` (Playwright, нужны запущенные сервисы), `make lint`.

## 2. Сервер (test и prod)

Требования: Ubuntu 24.04, 4 vCPU, 8 ГБ RAM, SSD; Docker Engine + compose plugin; домен, указывающий на сервер (A-запись для `example.com` и `test.example.com`); открытые порты 80/443.

```bash
# один раз на сервере
sudo apt-get update && sudo apt-get install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sudo sh
sudo mkdir -p /srv/dortech/{test,prod} && sudo chown -R $USER /srv/dortech
docker network create edge

# исходники (для каждого окружения свой каталог)
git clone git@github.com:rosavskiy/dortech.git /srv/dortech/prod/src
git clone git@github.com:rosavskiy/dortech.git /srv/dortech/test/src

# переменные окружения
cp /srv/dortech/prod/src/deploy/.env.example /srv/dortech/prod/.env && chmod 600 /srv/dortech/prod/.env
# заполнить: COMPOSE_PROJECT_NAME=dortech-prod, SECRET_KEY (openssl rand -hex 32), POSTGRES_PASSWORD, SITE_URL,
# NEXT_PUBLIC_SITE_URL, ALLOWED_HOSTS, ADMIN_URL_PATH, SMTP_*, NOTIFICATION_EMAILS, WEBHOOK_*, ENVIRONMENT=production
# аналогично для test: COMPOSE_PROJECT_NAME=dortech-test, ENVIRONMENT=test, ROBOTS_ALLOW=0, WEBHOOK_SINK_ENABLED=1

# прокси (Caddy): домены, email для Let's Encrypt, basic-auth тестовой среды
cp /srv/dortech/prod/src/deploy/edge.env.example /srv/dortech/prod/src/deploy/edge.env  # заполнить
docker run --rm caddy:2-alpine caddy hash-password --plaintext 'пароль-теста'           # → TEST_BASIC_HASH
cd /srv/dortech/prod/src && docker compose -f deploy/docker-compose.edge.yml up -d

# деплой
/srv/dortech/test/src/deploy/deploy.sh test main
/srv/dortech/prod/src/deploy/deploy.sh prod v1.0.0
```

После первого деплоя создайте администратора:

```bash
cd /srv/dortech/prod/src && docker compose --env-file /srv/dortech/prod/.env -f deploy/docker-compose.yml \
  exec backend python -m scripts.create_admin admin@example.com 'НадёжныйПароль1'
```

Обновление: `deploy.sh <env> <ref>` выполняет `git checkout`, сборку образов, миграции (`alembic upgrade head`), перезапуск и проверку `/api/health`. Прод принимает только теги `vX.Y.Z`.

Резервные копии: `sudo cp deploy/cron/dortech-backup /etc/cron.d/` (ежедневно 03:00, см. `RESTORE.md`).

## 3. Структура окружения на сервере

```
/srv/dortech/<env>/
├── src/        клон репозитория (deploy.sh переключает на нужный тег)
├── .env        секреты окружения (chmod 600)
├── media/      публичные файлы (картинки каталога и контента)
├── private/    файлы заявок (недоступны напрямую, отдаются после проверки прав)
├── logs/       app-error.log, backup.log
└── backups/    дампы БД и архивы media
```
