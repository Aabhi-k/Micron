import logging
from typing import Optional
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from app.core.config import settings

logger = logging.getLogger("backend.core.qdrant")

COLLECTION_NAME = "enterprise_knowledge"
VECTOR_SIZE = 1536

# Async Qdrant Client Singleton
qdrant_client: AsyncQdrantClient = AsyncQdrantClient(
    host=settings.QDRANT_HOST,
    port=settings.QDRANT_PORT,
)


def get_qdrant_client() -> AsyncQdrantClient:
    """Returns the singleton AsyncQdrantClient instance."""
    return qdrant_client


async def init_qdrant_collection(
    collection_name: str = COLLECTION_NAME, 
    vector_size: int = VECTOR_SIZE
) -> None:
    """
    Initializes the target Qdrant collection:
    1. Checks if collection exists.
    2. If not, creates it with specified vector size (default 1536) and Cosine distance.
    3. Creates payload keyword index for 'tenant_id' for strict isolated querying.
    """
    client = get_qdrant_client()
    try:
        exists = await client.collection_exists(collection_name=collection_name)
        if not exists:
            logger.info(
                f"Creating Qdrant collection '{collection_name}' "
                f"(size={vector_size}, distance=COSINE)..."
            )
            await client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE,
                ),
            )
            logger.info(f"Collection '{collection_name}' created successfully.")
        else:
            logger.info(f"Collection '{collection_name}' already exists.")

        # Create payload index for tenant_id for tenant filtering
        try:
            await client.create_payload_index(
                collection_name=collection_name,
                field_name="tenant_id",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            logger.info(f"Payload index for 'tenant_id' verified on '{collection_name}'.")
        except Exception as idx_err:
            logger.debug(f"Payload index status (tenant_id): {idx_err}")

        # Create payload index for project_id for multi-project isolation
        try:
            await client.create_payload_index(
                collection_name=collection_name,
                field_name="project_id",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            logger.info(f"Payload index for 'project_id' verified on '{collection_name}'.")
        except Exception as idx_err:
            logger.debug(f"Payload index status (project_id): {idx_err}")

    except Exception as e:
        logger.error(f"Failed to initialize Qdrant collection '{collection_name}': {e}")
        raise e


async def close_qdrant_client() -> None:
    """Closes the AsyncQdrantClient connection pool."""
    try:
        await qdrant_client.close()
        logger.info("Closed Qdrant client connection.")
    except Exception as e:
        logger.warning(f"Error closing Qdrant client: {e}")
