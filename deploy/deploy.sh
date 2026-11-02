#!/usr/bin/env bash
# Использование: deploy/deploy.sh <test|prod> <git-ref>
# Каталог окружения: /srv/dortech/<env>/{src,.env,media,private,logs,backups}
set -euo pipefail
ENV_NAME="${1:?test|prod}"; REF="${2:?git ref}"
ROOT="/srv/dortech/${ENV_NAME}"; SRC="${ROOT}/src"; ENV_FILE="${ROOT}/.env"
[[ -f "$ENV_FILE" ]] || { echo "нет ${ENV_FILE}"; exit 1; }
if [[ "$ENV_NAME" == "prod" && ! "$REF" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "prod принимает только теги vX.Y.Z"; exit 1
fi
cd "$SRC"
git fetch --all --tags --prune
git checkout -q --detach "$REF"
COMMIT=$(git rev-parse --short HEAD)
export GIT_COMMIT="$COMMIT" APP_VERSION="$REF"
mkdir -p "${ROOT}/media/public" "${ROOT}/private" "${ROOT}/logs" "${ROOT}/backups"
ln -sfn "$ENV_FILE" deploy/.env
ln -sfn "${ROOT}/media" deploy/media
ln -sfn "${ROOT}/private" deploy/private
ln -sfn "${ROOT}/logs" deploy/logs
COMPOSE=(docker compose --env-file "$ENV_FILE" -f deploy/docker-compose.yml)
"${COMPOSE[@]}" build --build-arg APP_VERSION="$REF" --build-arg GIT_COMMIT="$COMMIT"
"${COMPOSE[@]}" up -d postgres
"${COMPOSE[@]}" run --rm backend alembic upgrade head
"${COMPOSE[@]}" up -d --remove-orphans
sleep 5
"${COMPOSE[@]}" exec -T backend python -c "import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:8000/api/health').read().decode())"
echo "deploy ${ENV_NAME} ${REF} (${COMMIT}) ok"
