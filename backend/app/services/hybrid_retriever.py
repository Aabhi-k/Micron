import logging
from typing import List, Dict, Any, Optional
from qdrant_client import models
from app.core.config import settings
from app.core.security import validate_tenant_id
from app.services.embeddings import embedding_service
from app.services.qdrant_service import qdrant_service
from app.services.bm25_service import bm25_service
from app.services.reranker import reranker_service

logger = logging.getLogger("backend.services.hybrid_retriever")

class HybridRetriever:
    """Enterprise Hybrid Search Engine combining Dense Vector Search (Qdrant),
    Sparse Keyword Search (BM25), Reciprocal Rank Fusion (RRF, k=60),
    and Cross-Encoder Re-ranking with hard tenant isolation.
    """

    def __init__(self, collection_name: Optional[str] = None, rrf_k: Optional[int] = None):
        self.collection_name = collection_name or settings.QDRANT_COLLECTION
        self.rrf_k = rrf_k or settings.RRF_K

    async def index_documents(
        self,
        tenant_id: str,
        project_id: str,
        documents: List[Dict[str, Any]]
    ):
        """Index business process documents into both Qdrant and BM25 under the specified tenant."""
        tenant_id = validate_tenant_id(tenant_id)
        if not documents:
            return

        # 1. Update BM25 index
        bm25_service.index_documents(tenant_id=tenant_id, documents=documents)

        # 2. Dense embeddings generation & Qdrant upsert
        texts = [doc["content"] for doc in documents]
        embeddings = await embedding_service.embed_documents(texts)
        await qdrant_service.ensure_collection(
            collection_name=self.collection_name,
            vector_size=embedding_service.dimension
        )

        qdrant_points = []
        for i, doc in enumerate(documents):
            payload = doc.get("payload", {}).copy()
            payload["content"] = doc["content"]
            payload["project_id"] = project_id
            payload["tenant_id"] = tenant_id

            qdrant_points.append({
                "id": doc["id"],
                "vector": embeddings[i],
                "payload": payload
            })

        await qdrant_service.upsert_documents(
            tenant_id=tenant_id,
            collection_name=self.collection_name,
            points=qdrant_points
        )
        logger.info(f"Indexed {len(documents)} docs into Hybrid Search for tenant '{tenant_id}'.")

    async def retrieve(
        self,
        tenant_id: str,
        query: str,
        project_id: Optional[str] = None,
        top_k: int = 5,
        dense_candidates_count: int = 15,
        sparse_candidates_count: int = 15
    ) -> List[Dict[str, Any]]:
        """Executes tenant-isolated hybrid retrieval:
        1. Dense Qdrant search (filtered by tenant_id and optional project_id)
        2. Sparse BM25 search (scoped to tenant)
        3. Reciprocal Rank Fusion (RRF, k=60)
        4. Cross-Encoder Re-ranking
        """
        tenant_id = validate_tenant_id(tenant_id)
        logger.info(f"Hybrid retrieval initiated for tenant='{tenant_id}', query='{query}'")

        # Step 1: Dense Retrieval via Qdrant
        extra_filter = None
        if project_id:
            extra_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="project_id",
                        match=models.MatchValue(value=project_id)
                    )
                ]
            )

        query_vector = await embedding_service.embed_query(query)
        dense_results = await qdrant_service.search(
            tenant_id=tenant_id,
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=dense_candidates_count,
            extra_filter=extra_filter
        )

        # Step 2: Sparse Retrieval via BM25
        sparse_results = bm25_service.search(
            tenant_id=tenant_id,
            query=query,
            top_k=sparse_candidates_count
        )

        # Step 3: Reciprocal Rank Fusion (RRF)
        # RRF formula: Score(d) = sum_{m in {dense, sparse}} 1 / (k + rank_m(d))
        rrf_scores: Dict[str, float] = {}
        doc_registry: Dict[str, Dict[str, Any]] = {}

        for rank_idx, doc in enumerate(dense_results):
            doc_id = str(doc["id"])
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (self.rrf_k + (rank_idx + 1)))
            doc_registry[doc_id] = {
                "id": doc_id,
                "content": doc.get("payload", {}).get("content", ""),
                "payload": doc.get("payload", {}),
                "dense_score": doc.get("score")
            }

        for rank_idx, doc in enumerate(sparse_results):
            doc_id = str(doc["id"])
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (self.rrf_k + (rank_idx + 1)))
            if doc_id not in doc_registry:
                doc_registry[doc_id] = {
                    "id": doc_id,
                    "content": doc["content"],
                    "payload": doc.get("payload", {}),
                    "sparse_score": doc.get("score")
                }
            else:
                doc_registry[doc_id]["sparse_score"] = doc.get("score")

        # Sort candidates by RRF score descending
        sorted_doc_ids = sorted(rrf_scores.keys(), key=lambda did: rrf_scores[did], reverse=True)
        fused_candidates = []
        for did in sorted_doc_ids:
            item = doc_registry[did]
            item["rrf_score"] = rrf_scores[did]
            fused_candidates.append(item)

        if not fused_candidates:
            logger.info(f"No hybrid candidates found for tenant '{tenant_id}'.")
            return []

        # Step 4: Cross-Encoder Re-ranking
        top_pool = fused_candidates[: max(top_k * 2, 10)]
        final_ranked = await reranker_service.rerank(
            query=query,
            candidates=top_pool,
            top_k=top_k
        )

        return final_ranked

# Global singleton
hybrid_retriever = HybridRetriever()
