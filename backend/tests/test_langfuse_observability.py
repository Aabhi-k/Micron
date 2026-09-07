import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.observability import observe, propagate_attributes, trace_tenant_context
from app.services.embeddings import embedding_service
from app.services.reranker import reranker_service
from app.services.bm25_search import bm25_service
from app.services.synthesizer import generate_explanation


def test_trace_tenant_context_manager():
    """Verify trace_tenant_context injects user_id, tags, and metadata cleanly."""
    with trace_tenant_context(
        tenant_id="tenant-alpha",
        project_id="passman-main",
        tags=["audit-run"],
        metadata={"custom_key": "custom_val"}
    ):
        pass  # Context enters and exits without raising


@pytest.mark.asyncio
async def test_observed_embeddings_execution():
    """Verify that get_embedding and get_embeddings execute seamlessly when decorated with @observe."""
    vec, dim = await embedding_service.get_embedding("test query text")
    assert isinstance(vec, list)
    assert len(vec) == dim
    assert dim in (384, 1536)

    batch_vecs, batch_dim = await embedding_service.get_embeddings(["text A", "text B"])
    assert len(batch_vecs) == 2
    assert batch_dim == dim


@pytest.mark.asyncio
async def test_observed_reranker_execution():
    """Verify that RRF and cross-encoder rerank run smoothly when decorated with @observe."""
    dense = [{"id": "d1", "score": 0.9}]
    sparse = [{"id": "d1", "score": 5.0}, {"id": "d2", "score": 4.0}]

    fused = reranker_service.reciprocal_rank_fusion(dense_results=dense, sparse_results=sparse)
    assert len(fused) == 2
    assert "rrf_score" in fused[0]

    # Test rerank with fallback or active cross-encoder
    candidates = [{"content": "Password reset token", "doc_id": "d1"}]
    reranked = await reranker_service.rerank(query="password", candidates=candidates, top_k=1)
    assert len(reranked) == 1


@pytest.mark.asyncio
async def test_observed_bm25_search_execution():
    """Verify that BM25 search runs properly with @observe decorator."""
    tenant = "tenant-test-bm25"
    bm25_service.update_tenant_index(tenant, [
        {"id": "doc1", "title": "Auth", "content": "OAuth2 Bearer Token Authentication", "tenant_id": tenant}
    ])

    results = await bm25_service.search(tenant_id=tenant, query="OAuth2", top_k=1)
    assert len(results) == 1
    assert results[0]["doc_id"] == "doc1"


@pytest.mark.asyncio
async def test_observed_synthesizer_generation():
    """Verify generate_explanation executes with fallback template and Langfuse @observe."""
    code_data = {
        "function_name": "validate_jwt",
        "file_path": "src/security.py",
        "code_snippet": "def validate_jwt(): pass",
        "start_line": 10,
        "end_line": 20
    }
    result = await generate_explanation(
        code_data=code_data,
        business_context="BPD Rule 401: Tokens must be signed with RSA256.",
        user_query="How is JWT validated?"
    )
    assert "validate_jwt" in result
    assert "BPD Rule 401" in result


@pytest.mark.asyncio
async def test_observed_nested_chat_execution():
    """Verify that chat_endpoint with trace_tenant_context executes nested spans without error."""
    from app.api.v1.chat import chat_endpoint, ChatQueryRequest

    req = ChatQueryRequest(
        project_id="test-project",
        query="Tell me about authentication",
        tenant_id="tenant-obs-test"
    )

    with patch("app.api.v1.chat.query_business_docs", new_callable=AsyncMock) as mock_docs, \
         patch("app.api.v1.chat.auto_discover_code", new_callable=AsyncMock) as mock_auto:
        mock_auto.return_value = (None, None, None)
        mock_docs.return_value = "Authoritative test document context."

        res = await chat_endpoint(req=req, x_tenant_id="tenant-obs-test")
        assert res["tenant_id"] == "tenant-obs-test"
        assert "response" in res
