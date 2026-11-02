FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
ARG APP_VERSION=dev
ARG GIT_COMMIT=unknown
ENV PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy \
    APP_VERSION=${APP_VERSION} GIT_COMMIT=${GIT_COMMIT} PATH="/app/.venv/bin:$PATH"
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
RUN mkdir -p media/public private logs
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
