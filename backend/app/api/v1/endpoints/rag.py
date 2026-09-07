import time
import logging
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, status
from app.schemas.rag import SearchRequest, SearchResponse, ChunkResult
from app.services.retrieval.hybrid_search import hybrid_retrieval

logger = logging.getLogger("backend.api.v1.rag")

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/search", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def search_rag(
    request: SearchRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID", description="Mandatory tenant isolation identifier")
) -> SearchResponse:
    """
    Executes hybrid RAG retrieval strictly isolated to the requesting tenant:
    - Dense vector search (Qdrant)
    - Sparse keyword search (BM25)
    - Reciprocal Rank Fusion (k=60)
    - Cross-Encoder re-ranking
    """
    if not x_tenant_id or not x_tenant_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Header 'X-Tenant-ID' must be provided and cannot be empty."
        )

    start_time = time.perf_counter()
    try:
        raw_results = await hybrid_retrieval(
            query=request.query,
            tenant_id=x_tenant_id,
            top_k=request.top_k,
            project_id=request.project_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Hybrid retrieval unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during hybrid retrieval execution."
        )

    latency_ms = (time.perf_counter() - start_time) * 1000.0

    chunk_results = [
        ChunkResult(
            chunk_id=str(item.get("chunk_id", "")),
            document_id=str(item.get("document_id", "")),
            content=str(item.get("content", "")),
            score=float(item.get("score", 0.0)),
            project_id=item.get("project_id")
        )
        for item in raw_results
    ]

    return SearchResponse(
        results=chunk_results,
        latency_ms=round(latency_ms, 2)
    )
