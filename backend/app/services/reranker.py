import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger("backend.services.reranker")

class ReRankingService:
    """Re-ranks retrieved candidate passages using a deep Cross-Encoder model and RRF."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.CROSS_ENCODER_MODEL
        self._cross_encoder = None

    def _get_cross_encoder(self):
        if self._cross_encoder is None:
            try:
                from sentence_transformers import CrossEncoder
                logger.info(f"Loading CrossEncoder model: {self.model_name}")
                self._cross_encoder = CrossEncoder(self.model_name)
            except Exception as e:
                logger.warning(f"Failed to load CrossEncoder model '{self.model_name}': {e}")
                self._cross_encoder = None
        return self._cross_encoder

    def reciprocal_rank_fusion(
        self,
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        k: int = 60
    ) -> List[Dict[str, Any]]:
        """Compute Reciprocal Rank Fusion scores across dense and sparse ranking sets."""
        rrf_scores: Dict[str, float] = {}
        doc_registry: Dict[str, Dict[str, Any]] = {}

        # Dense ranking: 1 / (k + rank)
        for rank_idx, doc in enumerate(dense_results, start=1):
            doc_id = str(doc.get("doc_id") or doc.get("id"))
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + rank_idx))
            if doc_id not in doc_registry:
                doc_registry[doc_id] = doc.copy()

        # Sparse ranking: 1 / (k + rank)
        for rank_idx, doc in enumerate(sparse_results, start=1):
            doc_id = str(doc.get("doc_id") or doc.get("id"))
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + rank_idx))
            if doc_id not in doc_registry:
                doc_registry[doc_id] = doc.copy()

        sorted_doc_ids = sorted(rrf_scores.keys(), key=lambda did: rrf_scores[did], reverse=True)
        fused = []
        for did in sorted_doc_ids:
            item = doc_registry[did].copy()
            item["rrf_score"] = rrf_scores[did]
            fused.append(item)
        return fused

    async def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Compute cross-attention scores for (query, doc_content) pairs and sort descending."""
        if not candidates:
            return []

        model = self._cross_encoder or self._get_cross_encoder()
        if model is None:
            logger.info("CrossEncoder unavailable; retaining existing ordering.")
            return candidates[:top_k]

        try:
            pairs = []
            for doc in candidates:
                content = doc.get("content") or doc.get("payload", {}).get("content", "")
                pairs.append((query, content))

            scores = model.predict(pairs)

            reranked = []
            for i, doc in enumerate(candidates):
                doc_copy = doc.copy()
                score_val = float(scores[i])
                doc_copy["cross_encoder_score"] = score_val
                doc_copy["rerank_score"] = score_val
                reranked.append(doc_copy)

            reranked.sort(key=lambda x: x["cross_encoder_score"], reverse=True)
            return reranked[:top_k]

        except Exception as e:
            logger.warning(f"Error during cross-encoder reranking: {e}. Falling back to input order.")
            return candidates[:top_k]

# Aliases and singleton
RerankerService = ReRankingService
reranker_service = ReRankingService()
