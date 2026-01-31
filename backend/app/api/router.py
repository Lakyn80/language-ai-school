from fastapi import APIRouter

from app.modules.health.router import router as health_router
from app.modules.titles.router import router as titles_router
from app.modules.rag.router import router as rag_router
from app.modules.lessons.router import router as lessons_router
from app.modules.scenes.router import router as scenes_router
from app.modules.reading.router import router as reading_router

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

api_router.include_router(
    rag_router,
    prefix="/rag",
    tags=["rag"]
)

api_router.include_router(
    lessons_router,
    prefix="/lessons",
    tags=["lessons"]
)

api_router.include_router(
    scenes_router,
    prefix="/scenes",
    tags=["scenes"]
)

api_router.include_router(
    reading_router,
    prefix="/reading",
    tags=["reading"]
)
