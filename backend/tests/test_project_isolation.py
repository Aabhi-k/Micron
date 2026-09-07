import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.qdrant_service import QdrantService
from app.services.bm25_search import BM25SearchService
from app.services.retrieval.hybrid_search import hybrid_retrieval
from app.db.tenant_guard import TenantIsolationError


@pytest.mark.asyncio
async def test_cross_project_isolation_within_same_tenant():
    """
    Verifies that under the SAME tenant, querying for Project A returns
    strictly Project A chunks and NEVER leaks Project B chunks.
    """
    from app.services.bm25_search import bm25_service

    tenant_id = "tenant_enterprise"

    # Setup BM25 docs for two distinct projects under the same tenant
    bm25_service.update_tenant_index(tenant_id, [
        {
            "id": "chunk_auth_1",
            "doc_id": "doc_auth_1",
            "tenant_id": tenant_id,
            "project_id": "auth-service",
            "content": "Auth Service: JWT authentication with RSA256 signature verification"
        },
        {
            "id": "chunk_pay_1",
            "doc_id": "doc_pay_1",
            "tenant_id": tenant_id,
            "project_id": "payment-service",
            "content": "Payment Service: Stripe checkout webhook with signature HMAC-SHA256"
        }
    ])

    # Mock Qdrant client returning points matching project filter
    mock_point_auth = MagicMock()
    mock_point_auth.id = "chunk_auth_1"
    mock_point_auth.score = 0.95
    mock_point_auth.payload = {
        "tenant_id": tenant_id,
        "project_id": "auth-service",
        "document_id": "doc_auth_1",
        "content": "Auth Service: JWT authentication with RSA256 signature verification"
    }

    mock_point_pay = MagicMock()
    mock_point_pay.id = "chunk_pay_1"
    mock_point_pay.score = 0.95
    mock_point_pay.payload = {
        "tenant_id": tenant_id,
        "project_id": "payment-service",
        "document_id": "doc_pay_1",
        "content": "Payment Service: Stripe checkout webhook with signature HMAC-SHA256"
    }

    async def mock_query_points(collection_name, query, query_filter, limit, with_payload):
        # Inspect filter
        filter_keys = {c.key: c.match.value for c in (query_filter.must if query_filter else [])}
        target_proj = filter_keys.get("project_id")
        if target_proj == "auth-service":
            return MagicMock(points=[mock_point_auth])
        elif target_proj == "payment-service":
            return MagicMock(points=[mock_point_pay])
        return MagicMock(points=[])

    mock_qdrant = AsyncMock()
    mock_qdrant.collection_exists.return_value = True
    mock_qdrant.query_points.side_effect = mock_query_points

    with patch("app.services.retrieval.hybrid_search.get_qdrant_client", return_value=mock_qdrant):
        # 1. Search for auth-service
        auth_results = await hybrid_retrieval(
            query="JWT authentication signature",
            tenant_id=tenant_id,
            project_id="auth-service",
            top_k=5
        )

        assert len(auth_results) > 0
        for r in auth_results:
            assert r["project_id"] == "auth-service"
            assert "payment" not in r["content"].lower()
            assert "stripe" not in r["content"].lower()

        # 2. Search for payment-service
        pay_results = await hybrid_retrieval(
            query="Stripe checkout webhook",
            tenant_id=tenant_id,
            project_id="payment-service",
            top_k=5
        )

        assert len(pay_results) > 0
        for r in pay_results:
            assert r["project_id"] == "payment-service"
            assert "auth service" not in r["content"].lower()
            assert "rsa256" not in r["content"].lower()


@pytest.mark.asyncio
async def test_cross_tenant_isolation_with_same_project_name():
    """
    Verifies that two tenants sharing the SAME project identifier name (e.g. 'core-engine')
    can NEVER retrieve each other's data.
    """
    from app.services.bm25_search import bm25_service

    shared_proj = "core-engine"
    tenant_a = "tenant_alpha_org"
    tenant_b = "tenant_beta_org"

    bm25_service.update_tenant_index(tenant_a, [
        {
            "id": "chunk_a",
            "doc_id": "doc_a",
            "tenant_id": tenant_a,
            "project_id": shared_proj,
            "content": "Tenant Alpha proprietary secret cipher: ALPHA_SECRET_999"
        }
    ])

    bm25_service.update_tenant_index(tenant_b, [
        {
            "id": "chunk_b",
            "doc_id": "doc_b",
            "tenant_id": tenant_b,
            "project_id": shared_proj,
            "content": "Tenant Beta proprietary financial forecast: BETA_PROFIT_777"
        }
    ])

    mock_point_a = MagicMock()
    mock_point_a.id = "chunk_a"
    mock_point_a.score = 0.92
    mock_point_a.payload = {
        "tenant_id": tenant_a,
        "project_id": shared_proj,
        "document_id": "doc_a",
        "content": "Tenant Alpha proprietary secret cipher: ALPHA_SECRET_999"
    }

    mock_point_b = MagicMock()
    mock_point_b.id = "chunk_b"
    mock_point_b.score = 0.92
    mock_point_b.payload = {
        "tenant_id": tenant_b,
        "project_id": shared_proj,
        "document_id": "doc_b",
        "content": "Tenant Beta proprietary financial forecast: BETA_PROFIT_777"
    }

    async def mock_query_points(collection_name, query, query_filter, limit, with_payload):
        filter_keys = {c.key: c.match.value for c in (query_filter.must if query_filter else [])}
        if filter_keys.get("tenant_id") == tenant_a:
            return MagicMock(points=[mock_point_a])
        elif filter_keys.get("tenant_id") == tenant_b:
            return MagicMock(points=[mock_point_b])
        return MagicMock(points=[])

    mock_qdrant = AsyncMock()
    mock_qdrant.collection_exists.return_value = True
    mock_qdrant.query_points.side_effect = mock_query_points

    with patch("app.services.retrieval.hybrid_search.get_qdrant_client", return_value=mock_qdrant):
        # Query under Tenant A
        res_a = await hybrid_retrieval(
            query="proprietary confidential data",
            tenant_id=tenant_a,
            project_id=shared_proj,
            top_k=5
        )
        assert len(res_a) > 0
        all_content_a = " ".join([r["content"] for r in res_a])
        assert "ALPHA_SECRET_999" in all_content_a
        assert "BETA_PROFIT_777" not in all_content_a
        assert "beta" not in all_content_a.lower()

        # Query under Tenant B
        res_b = await hybrid_retrieval(
            query="proprietary confidential data",
            tenant_id=tenant_b,
            project_id=shared_proj,
            top_k=5
        )
        assert len(res_b) > 0
        all_content_b = " ".join([r["content"] for r in res_b])
        assert "BETA_PROFIT_777" in all_content_b
        assert "ALPHA_SECRET_999" not in all_content_b
        assert "alpha" not in all_content_b.lower()


@pytest.mark.asyncio
async def test_qdrant_compound_filter_enforced():
    """Verify Qdrant vector search strictly includes both tenant_id and project_id in Filter."""
    service = QdrantService()
    mock_client = AsyncMock()
    service._client = mock_client

    mock_point_valid = MagicMock()
    mock_point_valid.id = "doc-p1"
    mock_point_valid.score = 0.95
    mock_point_valid.payload = {
        "tenant_id": "tenant-corp",
        "project_id": "project-frontend",
        "doc_id": "doc-p1",
        "title": "Frontend Arch",
        "content": "React and Tailwind architecture"
    }

    # Rogue point with matching tenant but WRONG project
    mock_point_rogue_project = MagicMock()
    mock_point_rogue_project.id = "doc-p2"
    mock_point_rogue_project.score = 0.99
    mock_point_rogue_project.payload = {
        "tenant_id": "tenant-corp",
        "project_id": "project-backend",
        "doc_id": "doc-p2",
        "title": "Backend Arch",
        "content": "FastAPI architecture"
    }

    mock_client.search.return_value = [mock_point_valid, mock_point_rogue_project]

    results = await service.search(
        tenant_id="tenant-corp",
        project_id="project-frontend",
        query_vector=[0.1] * 10,
        top_k=5
    )

    # Check filter passed to Qdrant client
    mock_client.search.assert_called_once()
    _, kwargs = mock_client.search.call_args
    query_filter = kwargs.get("query_filter")
    assert query_filter is not None
    filter_dict = {c.key: c.match.value for c in query_filter.must}
    assert filter_dict["tenant_id"] == "tenant-corp"
    assert filter_dict["project_id"] == "project-frontend"

    # Verify defense-in-depth dropped the rogue backend point
    assert len(results) == 1
    assert results[0]["project_id"] == "project-frontend"
    assert results[0]["doc_id"] == "doc-p1"


@pytest.mark.asyncio
async def test_bm25_project_filter_enforced():
    """Verify BM25 search strictly filters out non-matching project_id."""
    bm25 = BM25SearchService()

    bm25.update_tenant_index("tenant-xyz", [
        {"id": "doc-1", "tenant_id": "tenant-xyz", "project_id": "proj-1", "content": "Database migration script"},
        {"id": "doc-2", "tenant_id": "tenant-xyz", "project_id": "proj-2", "content": "Database optimization guide"},
        {"id": "doc-3", "tenant_id": "tenant-xyz", "project_id": None, "content": "Database general note"}
    ])

    results = await bm25.search("tenant-xyz", query="Database", project_id="proj-1", top_k=10)
    assert len(results) == 1
    assert results[0]["project_id"] == "proj-1"
    assert results[0]["doc_id"] == "doc-1"


@pytest.mark.asyncio
async def test_rag_api_endpoint_project_scoping():
    """Verify POST /rag/search passes project_id and returns project_id in ChunkResult."""
    from fastapi import FastAPI
    from httpx import AsyncClient, ASGITransport
    from app.api.v1.endpoints.rag import router as rag_router

    test_app = FastAPI()
    test_app.include_router(rag_router)

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        with patch("app.api.v1.endpoints.rag.hybrid_retrieval", return_value=[
            {
                "chunk_id": "c1",
                "document_id": "d1",
                "content": "Project scoped chunk",
                "score": 0.94,
                "tenant_id": "tenant_123",
                "project_id": "target_project"
            }
        ]) as mock_retrieve:
            resp = await client.post(
                "/rag/search",
                headers={"X-Tenant-ID": "tenant_123"},
                json={"query": "scoped query", "project_id": "target_project", "top_k": 3}
            )
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["results"]) == 1
            assert data["results"][0]["project_id"] == "target_project"
            assert data["results"][0]["content"] == "Project scoped chunk"

            mock_retrieve.assert_called_once_with(
                query="scoped query",
                tenant_id="tenant_123",
                top_k=3,
                project_id="target_project"
            )


@pytest.mark.asyncio
async def test_files_tenant_ownership_rejection():
    """Verify that accessing a project belonging to another tenant via files API is rejected."""
    from fastapi import FastAPI
    from httpx import AsyncClient, ASGITransport
    from app.api.v1.files import router as files_router
    from app.db.session import get_db
    import uuid

    test_app = FastAPI()
    test_app.include_router(files_router)

    # Mock DB session returning a project belonging to a different tenant
    mock_project = MagicMock()
    mock_project.id = "proj-forbidden"
    mock_project.tenant_id = uuid.UUID("99999999-9999-9999-9999-999999999999")

    mock_db = AsyncMock()
    mock_db_res = MagicMock()
    mock_db_res.scalars.return_value.first.return_value = mock_project
    mock_db.execute.return_value = mock_db_res

    test_app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        # Request with Tenant Alpha attempting to access proj-forbidden
        resp = await client.get(
            "/tree/proj-forbidden",
            headers={"X-Tenant-ID": "00000000-0000-0000-0000-000000000001"}
        )
        assert resp.status_code == 403
        assert "Access Denied" in resp.json()["detail"]
