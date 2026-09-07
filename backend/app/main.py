import sys
from pathlib import Path

# Ensure backend root is in sys.path regardless of execution method
_backend_dir = str(Path(__file__).resolve().parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import logging
import uuid
import os
from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.config import settings
from app.api.v1 import api_v1_router
from app.db.session import init_db, engine
from app.services.qdrant_service import qdrant_service
from app.core.redis import ping_redis, close_redis

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
    from app.core.qdrant import init_qdrant_collection
    await init_qdrant_collection()

    # 3. Verify Redis connection
    if await ping_redis():
        logger.info("Connected to Redis cache/broker.")
    else:
        logger.warning("Could not reach Redis cache/broker at startup.")

    # 4. Auto-ingest Passman BPD specification if present
    try:
        from app.db.session import async_session_factory
        from app.services.ingestion.auto_ingest import auto_ingest_passman_bpd
        async with async_session_factory() as session:
            await auto_ingest_passman_bpd(session)
    except Exception as ai_err:
        logger.warning(f"Passman BPD auto-ingest deferred: {ai_err}")

    yield

    logger.info("Shutting down Micron Backend Orchestrator...")
    await close_redis()
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

# Mount API version 1 routers (/projects, /files, /chat, /symbols, /documents)
app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/health", tags=["Health"])
async def health_check():
    redis_healthy = await ping_redis()
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "database": "postgresql+asyncpg",
        "vector_db": "qdrant (async)",
        "redis": "connected" if redis_healthy else "disconnected",
        "fusion": f"RRF (k={settings.RRF_K})",
        "reranker": settings.CROSS_ENCODER_MODEL,
        "observability": "langfuse-cloud" if "cloud.langfuse.com" in settings.LANGFUSE_HOST else settings.LANGFUSE_HOST
    }




if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
