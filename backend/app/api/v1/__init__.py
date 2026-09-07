from fastapi import APIRouter
from app.api.v1.projects import router as projects_router
from app.api.v1.files import router as files_router
from app.api.v1.chat import router as chat_router
from app.api.v1.symbols import router as symbols_router
from app.api.v1.documents import router as documents_router

api_v1_router = APIRouter()

api_v1_router.include_router(projects_router, prefix="/projects", tags=["Projects"])
api_v1_router.include_router(files_router, prefix="/files", tags=["Files"])
api_v1_router.include_router(chat_router, prefix="/chat", tags=["Chat & RAG"])
api_v1_router.include_router(symbols_router, prefix="/symbols", tags=["Symbols & AST"])
api_v1_router.include_router(documents_router, prefix="/documents", tags=["Documents & Hybrid RAG"])
