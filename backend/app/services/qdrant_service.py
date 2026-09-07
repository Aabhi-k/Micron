import logging
from typing import List, Dict, Any, Optional
from qdrant_client import AsyncQdrantClient, models
from app.core.config import settings
from app.db.tenant_guard import validate_tenant_id, TenantIsolationError

logger = logging.getLogger("backend.services.qdrant_service")

class QdrantService:
    """Async Qdrant vector store service with strict tenant isolation enforcement."""

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        self.host = host or settings.QDRANT_HOST
        self.port = port or settings.QDRANT_PORT
        self._client: Optional[AsyncQdrantClient] = None
        self._initialized_collections = set()

    def get_client(self) -> AsyncQdrantClient:
        if self._client is None:
            self._client = AsyncQdrantClient(host=self.host, port=self.port, timeout=10)
        return self._client

    async def close(self):
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def ensure_collection(self, collection_name: str, vector_size: int = 1536):
        """Idempotently create collection with cosine similarity."""
        client = self.get_client()
        try:
            collections = await client.get_collections()
            existing = [c.name for c in collections.collections]
            if collection_name not in existing:
                await client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=vector_size,
                        distance=models.Distance.COSINE
                    )
                )
                await client.create_payload_index(
                    collection_name=collection_name,
                    field_name="tenant_id",
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
                logger.info(f"Created Qdrant collection '{collection_name}' (vector size: {vector_size}).")
            self._initialized_collections.add(collection_name)
        except Exception as e:
            logger.warning(f"Failed to verify/create Qdrant collection '{collection_name}': {e}")

    async def upsert_documents(
        self,
        tenant_id: str,
        collection_name: str,
        points: List[Dict[str, Any]]
    ):
        """Upsert documents enforcing that payload contains matching tenant_id."""
        clean_tenant_id = validate_tenant_id(tenant_id)
        client = self.get_client()

        qdrant_points = []
        for p in points:
            payload = p.get("payload", {}).copy()
            payload["tenant_id"] = clean_tenant_id
            qdrant_points.append(
                models.PointStruct(
                    id=p["id"],
                    vector=p["vector"],
                    payload=payload
                )
            )

        try:
            await client.upsert(
                collection_name=collection_name,
                points=qdrant_points
            )
        except Exception as e:
            logger.error(f"Error upserting vectors into Qdrant for tenant {clean_tenant_id}: {e}")
            raise

    async def upsert_document(
        self,
        tenant_id: str,
        document_id: str,
        vector: List[float],
        title: str = "",
        content: str = "",
        project_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None
    ) -> bool:
        """Upsert a single document vector into Qdrant with tenant and project isolation."""
        coll = collection_name or settings.QDRANT_COLLECTION
        payload = {
            "title": title,
            "content": content,
            "project_id": str(project_id) if project_id else "",
            "metadata": metadata or {}
        }
        await self.upsert_documents(
            tenant_id=tenant_id,
            collection_name=coll,
            points=[{"id": document_id, "vector": vector, "payload": payload}]
        )
        return True

    async def search(
        self,
        tenant_id: str,
        query_vector: List[float],
        project_id: Optional[str] = None,
        collection_name: Optional[str] = None,
        top_k: int = 10,
        limit: Optional[int] = None,
        extra_filter: Optional[models.Filter] = None
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search strictly filtered by tenant_id and optional project_id."""
        clean_tenant_id = validate_tenant_id(tenant_id)
        collection = collection_name or settings.QDRANT_COLLECTION
        client = self.get_client()
        effective_limit = limit if limit is not None else top_k

        # Hard tenant isolation filter
        tenant_condition = models.FieldCondition(
            key="tenant_id",
            match=models.MatchValue(value=clean_tenant_id)
        )

        must_conditions = [tenant_condition]
        if project_id:
            must_conditions.append(
                models.FieldCondition(
                    key="project_id",
                    match=models.MatchValue(value=str(project_id))
                )
            )

        if extra_filter and extra_filter.must:
            must_conditions.extend(extra_filter.must)

        strict_filter = models.Filter(must=must_conditions)

        try:
            hits = await client.search(
                collection_name=collection,
                query_vector=query_vector,
                query_filter=strict_filter,
                limit=effective_limit
            )

            results = []
            for hit in hits:
                payload = hit.payload or {}
                # Defense-in-depth: discard point if payload tenant_id does not match
                if str(payload.get("tenant_id", clean_tenant_id)) != clean_tenant_id:
                    continue
                if project_id and str(payload.get("project_id", "")) != str(project_id):
                    continue

                doc_id = str(payload.get("doc_id") or payload.get("document_id") or hit.id)
                results.append({
                    "id": hit.id,
                    "doc_id": doc_id,
                    "score": hit.score,
                    "title": payload.get("title", ""),
                    "content": payload.get("content", ""),
                    "project_id": payload.get("project_id"),
                    "payload": payload
                })
            return results
        except Exception as e:
            logger.warning(f"Qdrant search error for tenant {clean_tenant_id}: {e}")
            return []


# Global singleton
qdrant_service = QdrantService()
