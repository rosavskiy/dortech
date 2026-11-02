#!/usr/bin/env bash
# Использование: deploy/restore.sh <test|prod> <путь к .dump>
# Останавливает приложение, пересоздаёт БД из дампа, применяет миграции, сверяет counts.json.
set -euo pipefail
ENV_NAME="${1:?test|prod}"; DUMP="${2:?dump}"
ROOT="/srv/dortech/${ENV_NAME}"; ENV_FILE="${ROOT}/.env"; SRC="${ROOT}/src"
# shellcheck disable=SC1090
set -a; source "$ENV_FILE"; set +a
COMPOSE=(docker compose --env-file "$ENV_FILE" -f "${SRC}/deploy/docker-compose.yml")
DB="${POSTGRES_DB:-dortech}"; U="${POSTGRES_USER:-dortech}"
[[ -f "${DUMP}.sha256" ]] && (cd "$(dirname "$DUMP")" && sha256sum -c "$(basename "$DUMP").sha256")
echo "== стоп приложения"; "${COMPOSE[@]}" stop backend worker frontend
echo "== пересоздание БД"
"${COMPOSE[@]}" exec -T postgres psql -U "$U" -d postgres -c "drop database if exists ${DB} with (force);"
"${COMPOSE[@]}" exec -T postgres psql -U "$U" -d postgres -c "create database ${DB} owner ${U};"
"${COMPOSE[@]}" exec -T postgres pg_restore -U "$U" -d "$DB" --no-owner --no-privileges < "$DUMP"
echo "== миграции"; "${COMPOSE[@]}" run --rm backend alembic upgrade head
if [[ -f "${DUMP}.counts.json" ]]; then
  echo "== сверка counts"; cat "${DUMP}.counts.json"; echo
  "${COMPOSE[@]}" exec -T postgres psql -U "$U" -d "$DB" -At -c \
    "select json_object_agg(t, c) from (select 'users' t, count(*) c from users union all select 'organizations', count(*) from organizations union all select 'equipment', count(*) from equipment union all select 'inquiries', count(*) from inquiries union all select 'attachments', count(*) from attachments) s;"
fi
echo "== старт"; "${COMPOSE[@]}" up -d
echo "restore ${ENV_NAME} из ${DUMP} завершён $(date -Is)"
