#!/usr/bin/env bash
# Использование: deploy/backup.sh <test|prod>
# Ежедневный дамп БД (pg_dump -Fc) + sha256 + counts.json; по воскресеньям — tar media/.
set -euo pipefail
ENV_NAME="${1:?test|prod}"
ROOT="/srv/dortech/${ENV_NAME}"; ENV_FILE="${ROOT}/.env"; SRC="${ROOT}/src"
# shellcheck disable=SC1090
set -a; source "$ENV_FILE"; set +a
STAMP=$(date +%Y%m%d-%H%M); DEST="${ROOT}/backups"; mkdir -p "$DEST"
COMPOSE=(docker compose --env-file "$ENV_FILE" -f "${SRC}/deploy/docker-compose.yml")
DUMP="${DEST}/${ENV_NAME}-${STAMP}.dump"
"${COMPOSE[@]}" exec -T postgres pg_dump -U "${POSTGRES_USER:-dortech}" -Fc "${POSTGRES_DB:-dortech}" > "$DUMP"
sha256sum "$DUMP" > "${DUMP}.sha256"
"${COMPOSE[@]}" exec -T postgres psql -U "${POSTGRES_USER:-dortech}" -d "${POSTGRES_DB:-dortech}" -At -c \
  "select json_object_agg(t, c) from (select 'users' t, count(*) c from users union all select 'organizations', count(*) from organizations union all select 'equipment', count(*) from equipment union all select 'inquiries', count(*) from inquiries union all select 'attachments', count(*) from attachments) s;" \
  > "${DUMP}.counts.json"
if [[ "$(date +%u)" == "7" ]]; then
  tar -czf "${DEST}/${ENV_NAME}-media-${STAMP}.tar.gz" -C "$ROOT" media private
fi
find "$DEST" -name "${ENV_NAME}-*.dump*" -mtime "+${BACKUP_RETENTION_DAYS:-14}" -delete
find "$DEST" -name "${ENV_NAME}-media-*.tar.gz" -mtime +56 -delete
echo "backup ${ENV_NAME} ${STAMP}: $(du -h "$DUMP" | cut -f1)"
