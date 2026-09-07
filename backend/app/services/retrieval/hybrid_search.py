import asyncio
import logging
from typing import List, Dict, Any, Optional
from qdrant_client.http import models
from app.core.qdrant import get_qdrant_client, COLLECTION_NAME
from app.services.embeddings import embedding_service
from app.services.bm25_search import bm25_service
from app.services.reranker import ReRankingService
from app.db.tenant_guard import validate_tenant_id, TenantIsolationError

logger = logging.getLogger("backend.services.retrieval.hybrid_search")

_reranker_service = ReRankingService()


async def hybrid_retrieval(
    query: str, 
    tenant_id: str, 
    top_k: int = 5,
    project_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Executes an enterprise-grade multi-stage hybrid retrieval strictly isolated to tenant_id and optional project_id:
    1. Hard Isolation Validation: Reject missing, empty, or whitespace-only tenant_id.
    2. Dense Vector Search: Qdrant vector search with mandatory tenant_id and optional project_id filter (top 25).
    3. Sparse BM25 Search: BM25 keyword search strictly isolated to tenant and project chunks (top 25).
    4. Reciprocal Rank Fusion (RRF): Merge rankings using RRF with constant k=60 (top 20).
    5. Cross-Encoder Re-ranking: Score candidates using cross-encoder/ms-marco-MiniLM-L-6-v2 (top_k).
    """
    # 1. Hard Isolation Validation
    if not tenant_id or not str(tenant_id).strip():
        raise ValueError("Tenant Isolation Violation: 'tenant_id' must be provided and cannot be empty.")

    try:
        clean_tenant_id = validate_tenant_id(tenant_id)
    except TenantIsolationError as e:
        raise ValueError(f"Tenant Isolation Violation: {e}") from e

    clean_query = (query or "").strip()
    if not clean_query:
        return []

    # 2. Dense Vector Search
    dense_candidates: List[Dict[str, Any]] = []
    try:
        client = get_qdrant_client()
        query_vector, _ = await embedding_service.get_embedding(clean_query)

        must_conditions = [
            models.FieldCondition(
                key="tenant_id",
                match=models.MatchValue(value=clean_tenant_id)
            )
        ]
        if project_id:
            must_conditions.append(
                models.FieldCondition(
                    key="project_id",
                    match=models.MatchValue(value=str(project_id))
                )
            )

        tenant_filter = models.Filter(must=must_conditions)

        collection_to_search = COLLECTION_NAME
        # Verify collection exists before querying
        if await client.collection_exists(collection_name=collection_to_search):
            # Dynamically adapt vector dimension to collection config if fallback model was used
            try:
                coll_info = await client.get_collection(collection_to_search)
                expected_dim = coll_info.config.params.vectors.size
                if len(query_vector) != expected_dim:
                    if len(query_vector) < expected_dim:
                        query_vector = (query_vector * (expected_dim // len(query_vector) + 1))[:expected_dim]
                    else:
                        query_vector = query_vector[:expected_dim]
            except Exception as dim_err:
                logger.debug(f"Dimension check warning: {dim_err}")

            if hasattr(client, "query_points"):
                response = await client.query_points(
                    collection_name=collection_to_search,
                    query=query_vector,
                    query_filter=tenant_filter,
                    limit=25,
                    with_payload=True
                )
                points = response.points
            else:
                points = await client.search(
                    collection_name=collection_to_search,
                    query_vector=query_vector,
                    query_filter=tenant_filter,
                    limit=25,
                    with_payload=True
                )

            for pt in points:
                payload = pt.payload or {}
                # Defense-in-depth: discard point if tenant_id doesn't match
                if str(payload.get("tenant_id", clean_tenant_id)) != clean_tenant_id:
                    continue
                # Defense-in-depth: discard point if project_id specified and doesn't match
                if project_id and str(payload.get("project_id", "")) != str(project_id):
                    continue

                chunk_id = str(pt.id)
                doc_id = str(payload.get("document_id") or chunk_id)
                content = str(payload.get("content", ""))
                score = float(pt.score) if pt.score is not None else 0.0

                dense_candidates.append({
                    "chunk_id": chunk_id,
                    "document_id": doc_id,
                    "content": content,
                    "score": score,
                    "tenant_id": clean_tenant_id,
                    "project_id": payload.get("project_id")
                })
        else:
            logger.warning(f"Qdrant collection '{collection_to_search}' not found for dense search.")

    except Exception as e:
        logger.warning(f"Dense vector search failed: {e}")

    # 3. Sparse BM25 Search
    sparse_candidates: List[Dict[str, Any]] = []
    try:
        bm25_raw_results = await bm25_service.search(
            tenant_id=clean_tenant_id,
            query=clean_query,
            top_k=25,
            project_id=project_id
        )
        for doc in bm25_raw_results:
            chunk_id = str(doc.get("chunk_id") or doc.get("doc_id") or doc.get("id"))
            doc_id = str(doc.get("document_id") or doc.get("doc_id") or chunk_id)
            doc_proj = doc.get("project_id")
            if project_id and str(doc_proj or "") != str(project_id):
                continue

            sparse_candidates.append({
                "chunk_id": chunk_id,
                "document_id": doc_id,
                "content": str(doc.get("content", "")),
                "score": float(doc.get("score", 0.0)),
                "tenant_id": clean_tenant_id,
                "project_id": doc_proj
            })
    except Exception as e:
        logger.warning(f"BM25 sparse search failed: {e}")

    # 4. Reciprocal Rank Fusion (RRF) with constant k=60
    # Formula: RRF_score = sum(1.0 / (60 + rank))
    K = 60
    rrf_scores: Dict[str, float] = {}
    candidate_map: Dict[str, Dict[str, Any]] = {}

    for rank, item in enumerate(dense_candidates, start=1):
        c_id = item["chunk_id"]
        rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (1.0 / (K + rank))
        if c_id not in candidate_map:
            candidate_map[c_id] = item

    for rank, item in enumerate(sparse_candidates, start=1):
        c_id = item["chunk_id"]
        rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (1.0 / (K + rank))
        if c_id not in candidate_map:
            candidate_map[c_id] = item

    # Extract top 20 fused candidates
    sorted_chunk_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)[:20]

    fused_candidates: List[Dict[str, Any]] = []
    for cid in sorted_chunk_ids:
        candidate = candidate_map[cid].copy()
        candidate["rrf_score"] = rrf_scores[cid]
        fused_candidates.append(candidate)

    if not fused_candidates:
        return []

    # 5. Re-ranking using Cross-Encoder (cross-encoder/ms-marco-MiniLM-L-6-v2)
    reranked = await _reranker_service.rerank(
        query=clean_query,
        candidates=fused_candidates,
        top_k=top_k
    )

    # Standardize output format
    output_chunks: List[Dict[str, Any]] = []
    for item in reranked:
        score = float(item.get("cross_encoder_score") or item.get("rrf_score") or item.get("score", 0.0))
        output_chunks.append({
            "chunk_id": item["chunk_id"],
            "document_id": item["document_id"],
            "content": item["content"],
            "score": score,
            "tenant_id": item["tenant_id"],
            "project_id": item.get("project_id")
        })

    return output_chunks
