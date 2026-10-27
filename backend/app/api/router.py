from fastapi import APIRouter

from app.api import catalog, content, health, inquiries

api_router = APIRouter()
api_router.include_router(health.router)

v1 = APIRouter(prefix="/v1")
v1.include_router(catalog.router)
v1.include_router(content.router)
v1.include_router(inquiries.router)
api_router.include_router(v1)
