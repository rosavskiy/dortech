# Эксплуатация

## Сервисы (docker compose, проект `dortech-prod` / `dortech-test`)

| Сервис | Назначение | Логи |
|---|---|---|
| `postgres` | БД PostgreSQL 16 | `docker compose logs postgres` |
| `backend` | FastAPI: API `/api`, панель `/<ADMIN_URL_PATH>` | stdout + `logs/app-error.log` (WARNING и выше, ротация 10 МБ × 5) |
| `worker` | очередь исходящих: email и webhook, повторы | stdout |
| `frontend` | Next.js | stdout |
| `caddy` (проект `dortech-edge`) | HTTPS, маршрутизация | `deploy/logs/caddy/*-access.log` (ротация 50 МБ) |

Команды (из `/srv/dortech/<env>/src`, `ENV=/srv/dortech/<env>/.env`):

```bash
C="docker compose --env-file $ENV -f deploy/docker-compose.yml"
$C ps                      # состояние
$C logs -f --tail=200 backend worker
$C exec backend python -m scripts.create_admin email пароль
$C exec backend python -m scripts.import_catalog /app/media/import/catalog.csv --dry-run
$C restart worker
curl -s https://домен/api/health   # {"status":"ok","version":"v1.0.0","commit":"…"}
```

## Очередь сообщений

Письма и webhook пишутся в таблицу `outbox` в той же транзакции, что и заявка; воркер отправляет их каждые 15 с. Статусы и ошибки видны в панели «Исходящие (email, webhook)». Повторы: 1 мин → 5 мин → 30 мин → 2 ч → 12 ч → 24 ч, затем `failed`. Переотправка: в панели сменить статус записи на «В очереди».

## Типовые ситуации

- **Письма не уходят** — проверить SMTP в `.env` и `logs` воркера; на тестовой среде письма ловит Mailpit (`http://localhost:8025` на сервере через SSH-туннель).
- **Пользователь заблокирован по ошибке** — панель → Пользователи → очистить «Заблокирован с».
- **Нужно сменить домен** — обновить `SITE_URL`, `NEXT_PUBLIC_SITE_URL`, `ALLOWED_HOSTS` в `.env`, `PROD_HOST` в `deploy/edge.env`, пересобрать: `deploy.sh prod <тег>` и `docker compose -f deploy/docker-compose.edge.yml up -d --force-recreate`.
- **Диск заполняется** — `backups/` чистится автоматически (14 дней); проверить `docker system prune` для старых образов.
- **Откат версии** — `deploy.sh prod vX.Y.Z` на предыдущий тег; миграции вниз не выполняются автоматически — при необходимости восстановить БД из дампа (`RESTORE.md`).

## Безопасность

Секреты только в `.env` (chmod 600). HTTPS с HSTS через Caddy. Панель по нестандартному пути `ADMIN_URL_PATH`; на test дополнительно basic-auth. Загрузки: белый список типов, проверка содержимого, до 20 МБ. Rate limit на вход/регистрацию/формы. Журнал существенных действий — панель «Журнал действий».
