from fastapi import APIRouter

from app.modules.health.router import router as health_router
from app.modules.titles.router import router as titles_router

api_router = APIRouter()

api_router.include_router(
    health_router,
    prefix="/health",
    tags=["health"]
)

api_router.include_router(
    titles_router,
    prefix="/titles",
    tags=["titles"]
)
