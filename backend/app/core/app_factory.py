from fastapi import FastAPI

from app.api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Language AI School API",
        description="Modular AI language-learning backend (RAG based)",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.include_router(
        api_router,
        prefix="/api"
    )

    return app
