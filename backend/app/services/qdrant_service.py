import logging
import uuid
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.db.tenant_guard import validate_tenant_id, TenantIsolationError

logger = logging.getLogger("backend.services.qdrant")

class QdrantService:
    """Asynchronous Qdrant client manager enforcing strict tenant isolation."""

    def __init__(self):
        self._client = None
        self._initialized_collections = set()

    async def get_client(self):
        """Lazily initialize the AsyncQdrantClient."""
        if self._client is None:
            try:
                from qdrant_client import AsyncQdrantClient
                self._client = AsyncQdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT,
                    timeout=10.0
                )
            except Exception as e:
                logger.warning(f"Failed to instantiate AsyncQdrantClient: {e}")
                return None
        return self._client

    async def ensure_collection(self, collection_name: str, vector_size: int = 1536) -> bool:
        """Ensures collection exists with proper vector size, distance metric, and payload indexes."""
        client = await self.get_client()
        if client is None:
            return False

        cache_key = f"{collection_name}:{vector_size}"
        if cache_key in self._initialized_collections:
            return True

        try:
            from qdrant_client.http import models

            exists = await client.collection_exists(collection_name=collection_name)
            if not exists:
                logger.info(f"Creating Qdrant collection '{collection_name}' with vector size {vector_size}...")
                await client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=vector_size,
                        distance=models.Distance.COSINE
                    )
                )

            # Ensure payload keyword index on tenant_id for high-performance isolated filtering
            try:
                await client.create_payload_index(
                    collection_name=collection_name,
                    field_name="tenant_id",
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
                await client.create_payload_index(
                    collection_name=collection_name,
                    field_name="project_id",
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
            except Exception:
                pass  # Index may already exist

            self._initialized_collections.add(cache_key)
            return True
        except Exception as e:
            logger.warning(f"Error ensuring Qdrant collection '{collection_name}': {e}")
            return False

    async def upsert_document(
        self,
        tenant_id: str,
        document_id: str,
        vector: List[float],
        content: str,
        title: str = "",
        project_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None
    ) -> bool:
        """Upserts a document vector with mandatory tenant_id in the payload."""
        clean_tenant_id = validate_tenant_id(tenant_id)
        coll = collection_name or settings.QDRANT_COLLECTION

        client = await self.get_client()
        if client is None:
            logger.warning("Qdrant client not available; skipping vector upsert.")
            return False

        await self.ensure_collection(coll, vector_size=len(vector))

        try:
            from qdrant_client.http import models

            # Generate consistent point ID
            try:
                point_id = str(uuid.UUID(document_id))
            except (ValueError, AttributeError):
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{clean_tenant_id}:{document_id}"))

            payload = {
                "tenant_id": clean_tenant_id,
                "project_id": str(project_id) if project_id else "",
                "doc_id": str(document_id),
                "title": title,
                "content": content,
                "metadata": metadata or {}
            }

            point = models.PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )

            await client.upsert(
                collection_name=coll,
                points=[point]
            )
            return True
        except Exception as e:
            logger.error(f"Error upserting vector for document {document_id}: {e}")
            return False

    async def search(
        self,
        tenant_id: str,
        query_vector: List[float],
        top_k: int = 10,
        project_id: Optional[str] = None,
        collection_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes vector similarity search with HARD tenant metadata isolation.
        Under NO circumstance will queries without matching tenant_id return data.
        """
        clean_tenant_id = validate_tenant_id(tenant_id)
        coll = collection_name or settings.QDRANT_COLLECTION

        client = await self.get_client()
        if client is None:
            logger.warning("Qdrant client unavailable; returning empty search results.")
            return []

        try:
            from qdrant_client.http import models

            must_conditions = [
                models.FieldCondition(
                    key="tenant_id",
                    match=models.MatchValue(value=clean_tenant_id)
                )
            ]

            if project_id:
                must_conditions.append(
                    models.FieldCondition(
                        key="project_id",
                        match=models.MatchValue(value=str(project_id))
                    )
                )

            tenant_filter = models.Filter(must=must_conditions)

            # Perform isolated vector search
            if hasattr(client, "search"):
                results = await client.search(
                    collection_name=coll,
                    query_vector=query_vector,
                    query_filter=tenant_filter,
                    limit=top_k,
                    with_payload=True
                )
            else:
                response = await client.query_points(
                    collection_name=coll,
                    query=query_vector,
                    query_filter=tenant_filter,
                    limit=top_k,
                    with_payload=True
                )
                results = response.points

            records = []
            for hit in results:
                payload = getattr(hit, "payload", {}) or {}
                # Defense-in-depth: assert matching tenant_id
                if payload.get("tenant_id") == clean_tenant_id:
                    records.append({
                        "doc_id": payload.get("doc_id", str(hit.id)),
                        "score": float(hit.score),
                        "title": payload.get("title", ""),
                        "content": payload.get("content", ""),
                        "project_id": payload.get("project_id"),
                        "metadata": payload.get("metadata", {})
                    })
                else:
                    logger.critical(
                        f"CRITICAL: Tenant isolation breach prevented! "
                        f"Expected {clean_tenant_id}, got {payload.get('tenant_id')}"
                    )
            return records

        except Exception as e:
            logger.warning(f"Vector search failed or collection '{coll}' not found: {e}")
            return []

    async def close(self):
        """Closes the underlying client connection."""
        if self._client is not None:
            await self._client.close()
            self._client = None

qdrant_service = QdrantService()
