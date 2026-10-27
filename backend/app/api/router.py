from fastapi import APIRouter

from app.api import account, auth, catalog, content, files, health, imports, inquiries, manager, webhook_sink

api_router = APIRouter()
api_router.include_router(health.router)

v1 = APIRouter(prefix="/v1")
v1.include_router(catalog.router)
v1.include_router(content.router)
v1.include_router(inquiries.router)
v1.include_router(auth.router)
v1.include_router(account.router)
v1.include_router(manager.router)
v1.include_router(files.router)
v1.include_router(imports.router)
v1.include_router(webhook_sink.router)
api_router.include_router(v1)
