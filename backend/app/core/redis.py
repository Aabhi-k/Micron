import logging
from typing import Optional
import redis.asyncio as aioredis
from app.core.config import settings
from app.db.tenant_guard import validate_tenant_id

logger = logging.getLogger("backend.redis")

_redis_client: Optional[aioredis.Redis] = None


def get_redis_client() -> aioredis.Redis:
    """Returns or initializes the singleton async Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
    return _redis_client


async def ping_redis() -> bool:
    """Ping Redis to verify connectivity."""
    try:
        client = get_redis_client()
        return await client.ping()
    except Exception as e:
        logger.warning(f"Redis ping failed: {e}")
        return False


async def close_redis() -> None:
    """Closes the Redis connection pool."""
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.aclose()
            logger.info("Closed Redis connection pool.")
        except Exception as e:
            logger.warning(f"Error closing Redis connection: {e}")
        finally:
            _redis_client = None


def get_tenant_cache_key(tenant_id: str, namespace: str, key: str) -> str:
    """
    Constructs a strictly isolated cache key:
    `tenant:{tenant_id}:{namespace}:{key}`
    """
    valid_tenant = validate_tenant_id(tenant_id)
    return f"tenant:{valid_tenant}:{namespace}:{key}"
