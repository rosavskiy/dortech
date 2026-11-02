.PHONY: up down migrate seed test e2e lint load backend frontend

up:            ## Поднять PostgreSQL и Mailpit локально
	docker compose -f deploy/docker-compose.dev.yml up -d

down:
	docker compose -f deploy/docker-compose.dev.yml down

migrate:       ## Применить миграции
	cd backend && uv run alembic upgrade head

seed:          ## Загрузить демо-данные
	cd backend && uv run python -m scripts.seed_demo

backend:       ## Dev-сервер API на :8000
	cd backend && uv run uvicorn app.main:app --reload --port 8000

frontend:      ## Dev-сервер Next.js на :3000
	cd frontend && npm run dev

worker:        ## Воркер outbox (email, webhook)
	cd backend && uv run python -m app.worker

test:          ## Тесты бэкенда
	cd backend && uv run pytest -q

e2e:           ## Playwright
	cd frontend && npx playwright test

lint:
	cd backend && uv run ruff check . && uv run ruff format --check .
	cd frontend && npm run lint

load:          ## Нагрузочный сценарий k6
	k6 run load/catalog.js
