from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from starlette.middleware.sessions import SessionMiddleware

from app.admin.setup import create_admin
from app.api.router import api_router
from app.core.config import settings
from app.core.db import engine
from app.core.limiter import limiter
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    (settings.media_root / "public").mkdir(parents=True, exist_ok=True)
    settings.private_root.mkdir(parents=True, exist_ok=True)
    yield
    await engine.dispose()


app = FastAPI(
    title="Дортех API",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/api/docs",
    redoc_url=None,
    openapi_url=None if settings.is_production else "/api/openapi.json",
)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def _rate_limited(request: Request, exc: RateLimitExceeded):
    return JSONResponse({"detail": "Слишком много запросов, попробуйте позже"}, status_code=429)


app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="dt_admin",
    https_only=settings.is_production,
    same_site="lax",
    max_age=12 * 3600,
)

app.include_router(api_router, prefix="/api")
app.mount("/media/public", StaticFiles(directory=settings.media_root / "public", check_dir=False), name="media-public")

admin = create_admin()
admin.mount_to(app)
