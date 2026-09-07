import logging
import uuid
import os
from typing import List
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.core.config import settings
from app.api.v1 import api_v1_router
from app.db.session import init_db, engine
from app.services.qdrant_service import qdrant_service

class ChatRequest(BaseModel):
    query: str
    file_path: str

class ChatResponse(BaseModel):
    markdown: str
    sanitized_code: str
    citations: List[str]
    trace_id: str

def mock_mcp_read_and_redact(file_path: str) -> str:
    target_path = os.path.abspath(os.path.join(settings.STORAGE_BASE, file_path))
    if not target_path.startswith(str(settings.STORAGE_BASE)):
        raise HTTPException(status_code=403, detail="Forbidden: Path traversal")
    return "def authenticate_user():\n    # [REDACTED_CREDENTIAL]\n    return True"

def mock_rag_fetch_bpd(query: str, file_path: str) -> List[str]:
    return ["BPD-402: All API modules must authenticate tokens before processing."]

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger("backend.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Micron Backend Orchestrator...")
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
    logger.info("Shutting down Micron Backend...")

app = FastAPI(
    title=settings.APP_NAME,
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

@app.post("/api/v1/chat/generate", response_model=ChatResponse, tags=["Chat"])
async def generate_chat(request: ChatRequest):
    sanitized_code = mock_mcp_read_and_redact(request.file_path)
    bpds = mock_rag_fetch_bpd(request.query, request.file_path)
    trace_id = str(uuid.uuid4())
    markdown = f"# Legacy Documentation\n\n## Sanitized Context\n```python\n{sanitized_code}\n```\n\n## Applied Rules\n" + "\n".join(bpds)
    
    return ChatResponse(
        markdown=markdown,
        sanitized_code=sanitized_code,
        citations=bpds,
        trace_id=trace_id
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
