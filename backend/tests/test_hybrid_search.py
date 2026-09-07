import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.reranker import ReRankingService
from app.services.rag_engine import search_business_docs

def test_reciprocal_rank_fusion_k60():
    """Verify Reciprocal Rank Fusion calculation adheres exactly to k=60."""
    reranker = ReRankingService()

    dense_results = [
        {"doc_id": "doc-1", "title": "D1", "content": "Content 1"},  # Rank 1
        {"doc_id": "doc-2", "title": "D2", "content": "Content 2"},  # Rank 2
        {"doc_id": "doc-3", "title": "D3", "content": "Content 3"},  # Rank 3
    ]

    sparse_results = [
        {"doc_id": "doc-2", "title": "D2", "content": "Content 2"},  # Rank 1
        {"doc_id": "doc-1", "title": "D1", "content": "Content 1"},  # Rank 2
        {"doc_id": "doc-4", "title": "D4", "content": "Content 4"},  # Rank 3
    ]

    fused = reranker.reciprocal_rank_fusion(dense_results, sparse_results, k=60)

    # Document 1: 1/(60+1) + 1/(60+2) = 1/61 + 1/62
    expected_doc1_score = (1.0 / 61.0) + (1.0 / 62.0)

    # Document 2: 1/(60+2) + 1/(60+1) = 1/62 + 1/61
    expected_doc2_score = (1.0 / 62.0) + (1.0 / 61.0)

    # Document 3: 1/(60+3) = 1/63
    expected_doc3_score = 1.0 / 63.0

    # Document 4: 1/(60+3) = 1/63
    expected_doc4_score = 1.0 / 63.0

    # Verify scores within floating-point tolerance
    scores_by_id = {d["doc_id"]: d["rrf_score"] for d in fused}
    assert pytest.approx(scores_by_id["doc-1"], rel=1e-5) == expected_doc1_score
    assert pytest.approx(scores_by_id["doc-2"], rel=1e-5) == expected_doc2_score
    assert pytest.approx(scores_by_id["doc-3"], rel=1e-5) == expected_doc3_score
    assert pytest.approx(scores_by_id["doc-4"], rel=1e-5) == expected_doc4_score

    # First two results should be doc-1 and doc-2 (tied top score)
    top_ids = {fused[0]["doc_id"], fused[1]["doc_id"]}
    assert top_ids == {"doc-1", "doc-2"}

@pytest.mark.asyncio
async def test_cross_encoder_rerank():
    """Verify Cross-Encoder reorders candidates according to model predictions."""
    reranker = ReRankingService()

    candidates = [
        {"doc_id": "doc-low", "content": "Irrelevant text"},
        {"doc_id": "doc-high", "content": "Highly relevant safety procedure"}
    ]

    # Mock the cross encoder to return deterministic scores
    mock_ce = MagicMock()
    mock_ce.predict.return_value = [-2.5, 4.8]  # First is low, second is high
    reranker._cross_encoder = mock_ce

    results = await reranker.rerank(
        query="safety procedure",
        candidates=candidates,
        top_k=2
    )

    # High score should be ranked first
    assert results[0]["doc_id"] == "doc-high"
    assert results[0]["cross_encoder_score"] == 4.8
    assert results[1]["doc_id"] == "doc-low"
    assert results[1]["cross_encoder_score"] == -2.5

@pytest.mark.asyncio
async def test_hybrid_search_pipeline_end_to_end():
    """Verify end-to-end search pipeline combines dense, sparse, RRF, and re-ranking."""
    tenant_id = "tenant-prod"
    query = "database connection timeout"

    dense_docs = [
        {"doc_id": "doc-dense-1", "title": "DB Timeout Spec", "content": "Configure timeouts appropriately", "score": 0.9}
    ]
    sparse_docs = [
        {"doc_id": "doc-dense-1", "title": "DB Timeout Spec", "content": "Configure timeouts appropriately", "score": 1.5},
        {"doc_id": "doc-sparse-2", "title": "Network Spec", "content": "Network timeout settings", "score": 1.2}
    ]

    mock_ce = MagicMock()
    # Explicitly mock cross-encoder prediction to score doc-dense-1 highest
    mock_ce.predict.return_value = [5.2, 2.1]

    with patch("app.services.rag_engine.embedding_service.get_embedding", new_callable=AsyncMock) as mock_embed, \
         patch("app.services.rag_engine.qdrant_service.search", new_callable=AsyncMock) as mock_qdrant, \
         patch("app.services.rag_engine.bm25_service.search", new_callable=AsyncMock) as mock_bm25, \
         patch("app.services.rag_engine.reranker_service._get_cross_encoder", return_value=mock_ce):

        mock_embed.return_value = ([0.1] * 10, 10)
        mock_qdrant.return_value = dense_docs
        mock_bm25.return_value = sparse_docs

        results = await search_business_docs(
            tenant_id=tenant_id,
            query=query,
            top_k=2
        )

        assert len(results) == 2
        assert results[0]["doc_id"] == "doc-dense-1"
        assert results[0]["cross_encoder_score"] == 5.2
        assert results[1]["doc_id"] == "doc-sparse-2"
        assert results[1]["cross_encoder_score"] == 2.1
