import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.db.tenant_guard import validate_tenant_id, tenant_filter, tenant_select, TenantIsolationError
from app.models.document import BusinessDocument
from app.models.tenant import Tenant
from app.services.qdrant_service import QdrantService
from app.services.bm25_search import BM25SearchService
from app.services.rag_engine import search_business_docs

def test_validate_tenant_id():
    """Test validation of tenant_id inputs."""
    assert validate_tenant_id("tenant-123") == "tenant-123"
    assert validate_tenant_id("  tenant-abc  ") == "tenant-abc"

    with pytest.raises(TenantIsolationError, match="tenant_id must not be None"):
        validate_tenant_id(None)

    with pytest.raises(TenantIsolationError, match="tenant_id must not be empty"):
        validate_tenant_id("")

    with pytest.raises(TenantIsolationError, match="tenant_id must not be empty"):
        validate_tenant_id("   ")

def test_tenant_filter_and_select():
    """Test SQLAlchemy query filter scoping."""
    expr = tenant_filter(BusinessDocument, "tenant-alpha")
    # Verify the expression is compiled with the tenant_id check
    assert "business_documents.tenant_id =" in str(expr)

    stmt = tenant_select(BusinessDocument, "tenant-alpha")
    sql_str = str(stmt)
    assert "WHERE business_documents.tenant_id = :tenant_id_1" in sql_str

    # Test error when model lacks tenant_id
    with pytest.raises(TenantIsolationError, match="does not have a 'tenant_id' column"):
        tenant_filter(Tenant, "tenant-alpha")

@pytest.mark.asyncio
async def test_qdrant_hard_tenant_filter_enforced():
    """Verify Qdrant vector search strictly injects tenant_id filter and checks results."""
    service = QdrantService()

    # Empty tenant_id must raise TenantIsolationError
    with pytest.raises(TenantIsolationError):
        await service.search(tenant_id="", query_vector=[0.1] * 10)

    with pytest.raises(TenantIsolationError):
        await service.search(tenant_id=None, query_vector=[0.1] * 10)

    # Mock Qdrant client to inspect the Filter payload
    mock_client = AsyncMock()
    service._client = mock_client

    # Case 1: Search sends tenant_id filter
    mock_point_valid = MagicMock()
    mock_point_valid.id = "doc-1"
    mock_point_valid.score = 0.95
    mock_point_valid.payload = {
        "tenant_id": "tenant-alpha",
        "doc_id": "doc-1",
        "title": "Alpha Doc",
        "content": "Secret Alpha content"
    }

    # Case 2: Defense-in-depth: Point from different tenant should be blocked
    mock_point_rogue = MagicMock()
    mock_point_rogue.id = "doc-2"
    mock_point_rogue.score = 0.99
    mock_point_rogue.payload = {
        "tenant_id": "tenant-beta",
        "doc_id": "doc-2",
        "title": "Beta Doc",
        "content": "Secret Beta content"
    }

    mock_client.search.return_value = [mock_point_valid, mock_point_rogue]

    results = await service.search(
        tenant_id="tenant-alpha",
        query_vector=[0.1] * 10,
        top_k=5
    )

    # Verify search was called with a filter matching tenant-alpha
    mock_client.search.assert_called_once()
    _, kwargs = mock_client.search.call_args
    query_filter = kwargs.get("query_filter")
    assert query_filter is not None
    assert any(
        cond.key == "tenant_id" and cond.match.value == "tenant-alpha"
        for cond in query_filter.must
    )

    # Verify defense-in-depth filtered out rogue tenant-beta point
    assert len(results) == 1
    assert results[0]["doc_id"] == "doc-1"
    assert results[0]["title"] == "Alpha Doc"

@pytest.mark.asyncio
async def test_bm25_cross_tenant_isolation():
    """Verify BM25 index never leaks documents across tenants."""
    bm25 = BM25SearchService()

    # Index doc for Tenant Alpha
    bm25.update_tenant_index("tenant-alpha", [
        {"id": "doc-a1", "tenant_id": "tenant-alpha", "title": "Alpha Protocol", "content": "Critical procedure for alpha engine"}
    ])

    # Index doc for Tenant Beta
    bm25.update_tenant_index("tenant-beta", [
        {"id": "doc-b1", "tenant_id": "tenant-beta", "title": "Beta Protocol", "content": "Critical procedure for beta engine"}
    ])

    # Attempting to index a doc with mismatched tenant must raise
    with pytest.raises(TenantIsolationError):
        bm25.update_tenant_index("tenant-alpha", [
            {"id": "doc-rogue", "tenant_id": "tenant-beta", "title": "Rogue", "content": "Breach"}
        ])

    # Query Tenant Alpha for "Critical procedure"
    res_alpha = await bm25.search("tenant-alpha", query="Critical procedure", top_k=5)
    assert len(res_alpha) == 1
    assert res_alpha[0]["doc_id"] == "doc-a1"
    assert res_alpha[0]["tenant_id"] == "tenant-alpha"

    # Query Tenant Beta for "Critical procedure"
    res_beta = await bm25.search("tenant-beta", query="Critical procedure", top_k=5)
    assert len(res_beta) == 1
    assert res_beta[0]["doc_id"] == "doc-b1"
    assert res_beta[0]["tenant_id"] == "tenant-beta"

    # Querying without tenant_id must raise
    with pytest.raises(TenantIsolationError):
        await bm25.search("", query="Critical procedure")
