from typing import List, Optional
from pydantic import BaseModel, Field


class ChunkResult(BaseModel):
    chunk_id: str
    content: str
    score: float
    document_id: str
    project_id: Optional[str] = None


class SearchRequest(BaseModel):
    query: str = Field(..., description="Natural language search query")
    top_k: int = Field(default=5, ge=1, le=100, description="Top-k candidates to retrieve")
    project_id: Optional[str] = Field(default=None, description="Optional target project identifier for project-scoped retrieval")


class SearchResponse(BaseModel):
    results: List[ChunkResult]
    latency_ms: float


class DocumentUploadResponse(BaseModel):
    document_id: str
    status: str
    project_id: Optional[str] = None
