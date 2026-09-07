import asyncio
import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger("backend.services.reranker")

class ReRankingService:
    """Provides Reciprocal Rank Fusion (RRF) and Cross-Encoder Re-ranking."""

    def __init__(self):
        self._cross_encoder = None

    def _get_cross_encoder(self):
        if self._cross_encoder is None:
            try:
                from sentence_transformers import CrossEncoder
                logger.info(f"Loading Cross-Encoder model: {settings.CROSS_ENCODER_MODEL}")
                self._cross_encoder = CrossEncoder(settings.CROSS_ENCODER_MODEL)
            except Exception as e:
                logger.warning(f"Could not load CrossEncoder '{settings.CROSS_ENCODER_MODEL}': {e}")
                self._cross_encoder = None
        return self._cross_encoder

    def reciprocal_rank_fusion(
        self,
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Merges dense and sparse rankings using Reciprocal Rank Fusion (RRF) with constant k=60.
        Score formula: RRF(d) = sum(1 / (k + rank))
        """
        constant_k = k if k is not None else settings.RRF_K
        scores: Dict[str, float] = {}
        doc_map: Dict[str, Dict[str, Any]] = {}

        # Process dense ranking (1-indexed rank)
        for rank, doc in enumerate(dense_results, start=1):
            doc_id = str(doc.get("doc_id") or doc.get("id"))
            scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (constant_k + rank))
            if doc_id not in doc_map:
                doc_map[doc_id] = doc

        # Process sparse BM25 ranking (1-indexed rank)
        for rank, doc in enumerate(sparse_results, start=1):
            doc_id = str(doc.get("doc_id") or doc.get("id"))
            scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (constant_k + rank))
            if doc_id not in doc_map:
                doc_map[doc_id] = doc

        # Sort candidates by combined RRF score descending
        sorted_doc_ids = sorted(scores.keys(), key=lambda d_id: scores[d_id], reverse=True)

        fused_results = []
        for d_id in sorted_doc_ids:
            doc = doc_map[d_id].copy()
            doc["rrf_score"] = scores[d_id]
            fused_results.append(doc)

        return fused_results

    async def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Re-ranks RRF candidates using a Cross-Encoder (ms-marco-MiniLM-L-6-v2).
        Falls back smoothly to RRF order if the Cross-Encoder is not available.
        """
        if not candidates:
            return []

        ce = self._get_cross_encoder()
        if ce is None:
            logger.info("Cross-Encoder unavailable; returning top RRF candidates.")
            return candidates[:top_k]

        pairs = [[query, doc.get("content", "")] for doc in candidates]

        try:
            def _predict():
                scores = ce.predict(pairs)
                return [float(s) for s in scores]

            ce_scores = await asyncio.to_thread(_predict)

            reranked = []
            for doc, score in zip(candidates, ce_scores):
                doc_copy = doc.copy()
                doc_copy["cross_encoder_score"] = score
                reranked.append(doc_copy)

            reranked.sort(key=lambda x: x["cross_encoder_score"], reverse=True)
            return reranked[:top_k]

        except Exception as e:
            logger.warning(f"Cross-Encoder inference error: {e}. Falling back to RRF ranking.")
            return candidates[:top_k]

reranker_service = ReRankingService()
