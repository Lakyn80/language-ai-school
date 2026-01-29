from fastapi import APIRouter

from app.modules.health.router import router as health_router
from app.modules.titles.router import router as titles_router
from app.modules.rag.router import router as rag_router
from app.modules.lessons.router import router as lessons_router

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
