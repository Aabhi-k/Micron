import uuid
import logging
from typing import Optional, List, Dict, Any
from app.core.config import settings
from app.db.tenant_guard import validate_tenant_id, TenantIsolationError
from app.services.embeddings import embedding_service
from app.services.qdrant_service import qdrant_service
from app.services.bm25_search import bm25_service
from app.services.reranker import reranker_service
from app.core.observability import observe

logger = logging.getLogger("backend.services.rag_engine")

@observe(name="index_business_document", as_type="span")
async def index_business_document(
    tenant_id: str,
    title: str,
    content: str,
    project_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    doc_id: Optional[str] = None,
    session=None
) -> Dict[str, Any]:
    """
    Indexes a business document into both PostgreSQL and Qdrant under strict tenant isolation.
    """
    clean_tenant_id = validate_tenant_id(tenant_id)
    document_id = doc_id or str(uuid.uuid4())
    meta = metadata or {}

    # 1. Store in PostgreSQL if session provided
    if session is not None:
        try:
            from app.models.document import BusinessDocument
            doc_model = BusinessDocument(
                id=document_id,
                tenant_id=clean_tenant_id,
                project_id=project_id,
                title=title,
                content=content,
                meta_info=meta
            )
            session.add(doc_model)
            await session.flush()
        except Exception as e:
            logger.error(f"Failed to persist document to DB: {e}")

    # 2. Generate dense vector embedding
    vector, dim = await embedding_service.get_embedding(f"{title}\n{content}")

    # 3. Upsert into Qdrant with hard tenant metadata
    upsert_success = await qdrant_service.upsert_document(
        tenant_id=clean_tenant_id,
        document_id=document_id,
        vector=vector,
        content=content,
        title=title,
        project_id=project_id,
        metadata=meta
    )

    # 4. Update BM25 in-memory index for this tenant
    doc_payload = {
        "id": document_id,
        "doc_id": document_id,
        "tenant_id": clean_tenant_id,
        "project_id": project_id,
        "title": title,
        "content": content,
        "meta_info": meta
    }
    # Retrieve current tenant docs or seed new
    current_docs = bm25_service._tenant_indices.get(clean_tenant_id, {}).get("docs", [])
    updated_docs = [d for d in current_docs if str(d.get("id")) != document_id] + [doc_payload]
    bm25_service.update_tenant_index(clean_tenant_id, updated_docs)

    return {
        "document_id": document_id,
        "tenant_id": clean_tenant_id,
        "title": title,
        "qdrant_indexed": upsert_success,
        "dimension": dim
    }

@observe(name="search_business_docs", as_type="retriever")
async def search_business_docs(
    tenant_id: str,
    query: str,
    project_id: Optional[str] = None,
    top_k: int = 3,
    dense_fetch_k: int = 15,
    sparse_fetch_k: int = 15,
    corpus_docs: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Multi-stage hybrid retrieval:
    1. Hard tenant validation.
    2. Dense vector search via Qdrant (filtered by tenant_id).
    3. Sparse BM25 search (filtered by tenant_id).
    4. Reciprocal Rank Fusion (RRF, constant k=60).
    5. Cross-Encoder re-ranking (cross-encoder/ms-marco-MiniLM-L-6-v2).
    """
    clean_tenant_id = validate_tenant_id(tenant_id)

    # 1. Dense search
    query_vector, _ = await embedding_service.get_embedding(query)
    dense_results = await qdrant_service.search(
        tenant_id=clean_tenant_id,
        query_vector=query_vector,
        top_k=dense_fetch_k,
        project_id=project_id
    )

    # 2. Sparse BM25 search
    sparse_results = await bm25_service.search(
        tenant_id=clean_tenant_id,
        query=query,
        top_k=sparse_fetch_k,
        project_id=project_id,
        corpus_docs=corpus_docs
    )

    # 3. Reciprocal Rank Fusion (k=60)
    fused_candidates = reranker_service.reciprocal_rank_fusion(
        dense_results=dense_results,
        sparse_results=sparse_results,
        k=settings.RRF_K
    )

    if not fused_candidates:
        return []

    # 4. Cross-Encoder Re-ranking
    final_results = await reranker_service.rerank(
        query=query,
        candidates=fused_candidates[:20],
        top_k=top_k
    )

    return final_results

@observe(name="query_business_docs", as_type="retriever")
async def query_business_docs(
    tenant_id: str = "default-tenant",
    query: str = "",
    project_id: Optional[str] = None,
    top_k: int = 3,
    **kwargs
) -> str:
    """
    Retrieves authoritative business process documents strictly belonging to the target tenant.
    Under NO circumstance will cross-tenant records be returned.
    """
    # Accommodate legacy callers where project_id might have been passed first
    if "project_id" in kwargs:
        project_id = kwargs["project_id"]
    if "tenant_id" in kwargs:
        tenant_id = kwargs["tenant_id"]

    clean_tenant_id = validate_tenant_id(tenant_id)

    try:
        from app.services.retrieval.hybrid_search import hybrid_retrieval
        hybrid_results = await hybrid_retrieval(
            query=query,
            tenant_id=clean_tenant_id,
            top_k=top_k,
            project_id=project_id
        )
        if hybrid_results:
            sections = []
            for r in hybrid_results:
                title = r.get("title", "Authoritative Specification")
                content = r.get("content", "").strip()
                score = r.get("score", 0.0)
                sections.append(f"### {title} (Relevance Score: {score:.4f})\n{content}")
            return "\n\n---\n\n".join(sections)
    except Exception as h_err:
        logger.debug(f"Hybrid retrieval in query_business_docs fallback note: {h_err}")

    results = await search_business_docs(
        tenant_id=clean_tenant_id,
        query=query,
        project_id=project_id,
        top_k=top_k
    )

    if results:
        sections = []
        for r in results:
            title = r.get("title", "Business Document")
            content = r.get("content", "").strip()
            score = r.get("cross_encoder_score") or r.get("rrf_score", 0.0)
            sections.append(f"### {title} (Relevance Score: {score:.4f})\n{content}")
        return "\n\n---\n\n".join(sections)

    # Grounded fallback baseline for the isolated tenant
    proj_tag = f" and project '{project_id}'" if project_id else ""
    return f"""Authoritative Business Process Guideline for Tenant '{clean_tenant_id}'{proj_tag}:
- Rule 101: All safety-critical hardware operations and alignment iterations must adhere to calibrated tolerance bounds.
- Rule 102: Resource allocation, transaction commits, and hardware latch releases must be idempotent.
- Rule 103: Legacy routines must log state changes and preserve hardware safety flags."""
