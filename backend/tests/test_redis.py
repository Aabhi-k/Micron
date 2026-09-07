import pytest
from unittest.mock import AsyncMock, patch
from app.core.redis import get_tenant_cache_key, ping_redis, close_redis
from app.db.tenant_guard import TenantIsolationError


def test_get_tenant_cache_key():
    """Verify tenant cache key format and tenant isolation validation."""
    key = get_tenant_cache_key("tenant_100", "doc_cache", "summary_doc_1")
    assert key == "tenant:tenant_100:doc_cache:summary_doc_1"

    # Empty tenant must raise TenantIsolationError
    with pytest.raises(TenantIsolationError):
        get_tenant_cache_key("", "doc_cache", "summary_doc_1")

    with pytest.raises(TenantIsolationError):
        get_tenant_cache_key("   ", "doc_cache", "summary_doc_1")


@pytest.mark.asyncio
async def test_ping_redis_mocked():
    """Verify ping_redis handles client response correctly."""
    mock_client = AsyncMock()
    mock_client.ping.return_value = True

    with patch("app.core.redis.get_redis_client", return_value=mock_client):
        result = await ping_redis()
        assert result is True
        mock_client.ping.assert_awaited_once()


@pytest.mark.asyncio
async def test_close_redis():
    """Verify close_redis shuts down connection pool."""
    mock_client = AsyncMock()
    with patch("app.core.redis._redis_client", mock_client):
        await close_redis()
        mock_client.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_health_endpoint_redis_connected():
    """Verify health endpoint includes Redis connectivity status."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    with patch("app.main.ping_redis", return_value=True):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ok"
            assert data["redis"] == "connected"
