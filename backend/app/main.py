import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import api_v1_router
from app.db.session import init_db, engine
from app.services.qdrant_service import qdrant_service

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger("backend.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Micron Backend Orchestrator...")
    logger.info(f"Storage Base Path: {settings.STORAGE_BASE}")
    settings.STORAGE_BASE.mkdir(parents=True, exist_ok=True)

    # 1. Initialize Relational DB schema (PostgreSQL + asyncpg)
    await init_db()

    # 2. Ensure Qdrant Vector Collection exists with isolated indexes
    dim = 1536 if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("sk-placeholder") else 384
    await qdrant_service.ensure_collection(settings.QDRANT_COLLECTION, vector_size=dim)

    yield

    logger.info("Shutting down Micron Backend Orchestrator...")
    await qdrant_service.close()
    await engine.dispose()

app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise Legacy Code Documentation Platform (FastAPI + MCP + Hybrid Multi-Tenant RAG)",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API version 1 router
app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "database": "postgresql+asyncpg",
        "vector_db": "qdrant (async)",
        "fusion": f"RRF (k={settings.RRF_K})",
        "reranker": settings.CROSS_ENCODER_MODEL
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
