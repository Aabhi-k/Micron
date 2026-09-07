import io
import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document, DocumentChunk
from app.services.ingestion.chunker import chunk_text
from qdrant_client.http.models import PointStruct
from app.models.tenant import Tenant
from sqlalchemy import select
from app.core.config import settings
from app.core.qdrant import get_qdrant_client, COLLECTION_NAME as ENTERPRISE_COLLECTION

logger = logging.getLogger("backend.services.ingestion.indexer")


def extract_text_from_content(file_content: bytes, filename: str) -> str:
    """Extracts text from binary file content supporting PDF, MD, TXT, and plain text."""
    fname_lower = filename.lower()
    if fname_lower.endswith(".pdf") or file_content.startswith(b"%PDF"):
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_content))
            pages = []
            for i, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    pages.append(f"[Page {i}]\n{page_text}")
            if pages:
                return "\n\n".join(pages)
        except Exception as e:
            logger.warning(f"pypdf extraction failed for '{filename}': {e}. Falling back to raw decode.")

    return file_content.decode("utf-8", errors="ignore")


async def process_and_index_document(
    file_content: bytes, 
    filename: str, 
    tenant_id_str: str, 
    db: AsyncSession
) -> uuid.UUID:
    """
    Parses, chunks, embeds, and indexes a document in PostgreSQL and Qdrant:
    1. Extracts text from PDF / MD / TXT.
    2. Stores document & chunks in PostgreSQL.
    3. Generates embeddings and upserts points into Qdrant ('enterprise_knowledge').
    4. Updates in-memory BM25 index for immediate hybrid search.
    """
    try:
        try:
            tenant_uuid = uuid.UUID(tenant_id_str)
        except (ValueError, AttributeError):
            tenant_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, tenant_id_str)

        # Ensure tenant exists to avoid foreign key violations
        tenant_res = await db.execute(select(Tenant).where(Tenant.id == tenant_uuid))
        if not tenant_res.scalar_one_or_none():
            db.add(Tenant(id=tenant_uuid, name=f"Tenant {tenant_id_str}"))
            await db.commit()

        text = extract_text_from_content(file_content, filename)
        if not text.strip():
            raise ValueError(f"No extractable text found in '{filename}'.")

        doc = Document(tenant_id=tenant_uuid, filename=filename, status="processing")
        db.add(doc)
        await db.commit()
        await db.refresh(doc)

        from app.services.embeddings import embedding_service
        from app.services.bm25_search import bm25_service

        chunks = chunk_text(text)
        db_chunks = []
        qdrant_points = []
        bm25_payloads = []

        q_client = get_qdrant_client()
        expected_dim = 1536
        try:
            coll_info = await q_client.get_collection(ENTERPRISE_COLLECTION)
            expected_dim = coll_info.config.params.vectors.size
        except Exception:
            pass

        for i, chunk in enumerate(chunks):
            emb, _ = await embedding_service.get_embedding(chunk)
            # Ensure vector dimension matches Qdrant collection
            if len(emb) != expected_dim:
                if len(emb) < expected_dim:
                    emb = (emb * (expected_dim // len(emb) + 1))[:expected_dim]
                else:
                    emb = emb[:expected_dim]

            chunk_uuid = str(uuid.uuid4())

            # 1. PostgreSQL chunk record
            doc_chunk = DocumentChunk(
                document_id=doc.id,
                tenant_id=tenant_uuid,
                chunk_index=i,
                content=chunk
            )
            db_chunks.append(doc_chunk)

            # 2. Qdrant Dense Vector payload
            qdrant_points.append(PointStruct(
                id=chunk_uuid,
                vector=emb,
                payload={
                    "tenant_id": tenant_id_str,
                    "document_id": str(doc.id),
                    "content": chunk,
                    "title": filename
                }
            ))

            # 3. BM25 Sparse Search payload
            bm25_payloads.append({
                "id": chunk_uuid,
                "doc_id": str(doc.id),
                "tenant_id": tenant_id_str,
                "title": filename,
                "content": chunk,
                "meta_info": {}
            })

        db.add_all(db_chunks)
        await db.commit()

        # Upsert Dense Vectors into enterprise_knowledge collection
        try:
            if await q_client.collection_exists(ENTERPRISE_COLLECTION):
                await q_client.upsert(collection_name=ENTERPRISE_COLLECTION, points=qdrant_points)
        except Exception as q_err:
            logger.warning(f"Qdrant {ENTERPRISE_COLLECTION} upsert notice: {q_err}")

        try:
            if settings.QDRANT_COLLECTION != ENTERPRISE_COLLECTION and await q_client.collection_exists(settings.QDRANT_COLLECTION):
                col_info = await q_client.get_collection(settings.QDRANT_COLLECTION)
                target_dim = getattr(col_info.config.params.vectors, "size", None)
                if target_dim and target_dim != expected_dim:
                    adapted_points = []
                    for pt in qdrant_points:
                        v = pt.vector
                        if len(v) < target_dim:
                            v = (v * (target_dim // len(v) + 1))[:target_dim]
                        else:
                            v = v[:target_dim]
                        adapted_points.append(PointStruct(id=pt.id, vector=v, payload=pt.payload))
                    await q_client.upsert(collection_name=settings.QDRANT_COLLECTION, points=adapted_points)
                else:
                    await q_client.upsert(collection_name=settings.QDRANT_COLLECTION, points=qdrant_points)
        except Exception as q_err:
            logger.warning(f"Qdrant {settings.QDRANT_COLLECTION} upsert notice: {q_err}")

        # Upsert Sparse Vectors (BM25)
        current_docs = bm25_service._tenant_indices.get(tenant_id_str, {}).get("docs", [])
        bm25_service.update_tenant_index(tenant_id_str, current_docs + bm25_payloads)

        doc.status = "indexed"
        await db.commit()
        return doc.id

    except Exception as e:
        logger.error(f"Error indexing document '{filename}': {e}", exc_info=True)
        await db.rollback()
        try:
            doc = Document(tenant_id=tenant_uuid, filename=filename, status=f"failed: {str(e)}")
            db.add(doc)
            await db.commit()
        except Exception:
            await db.rollback()
        return None
