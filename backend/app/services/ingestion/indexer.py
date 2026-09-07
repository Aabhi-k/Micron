import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document, DocumentChunk
from app.services.ingestion.chunker import chunk_text
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct

from app.models.tenant import Tenant
from sqlalchemy import select

async def process_and_index_document(file_content: bytes, filename: str, tenant_id_str: str, db: AsyncSession):
    try:
        tenant_uuid = uuid.UUID(tenant_id_str)
        # Ensure tenant exists to avoid foreign key violations
        tenant_res = await db.execute(select(Tenant).where(Tenant.id == tenant_uuid))
        if not tenant_res.scalar_one_or_none():
            db.add(Tenant(id=tenant_uuid, name=f"Auto-Tenant {tenant_id_str}"))
            await db.commit()

        text = file_content.decode("utf-8", errors="ignore")
        
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
        
        from app.core.config import settings

        for i, chunk in enumerate(chunks):
            # 1. Get REAL embedding from Person B's service instead of zeros
            emb, _ = await embedding_service.get_embedding(chunk)
            chunk_uuid = str(uuid.uuid4())
            
            # 2. Postgres chunk record
            doc_chunk = DocumentChunk(
                document_id=doc.id,
                tenant_id=tenant_uuid,
                chunk_index=i,
                content=chunk
            )
            db_chunks.append(doc_chunk)
            
            # 3. Qdrant Dense Vector payload
            qdrant_points.append(PointStruct(
                id=chunk_uuid,
                vector=emb,
                payload={"tenant_id": tenant_id_str, "document_id": str(doc.id), "content": chunk, "title": filename}
            ))
            
            # 4. BM25 Sparse Search payload
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
        
        # Upsert Dense Vectors
        q_client = QdrantClient(url="http://localhost:6333")
        q_client.upsert(collection_name=settings.QDRANT_COLLECTION, points=qdrant_points)
        
        # Upsert Sparse Vectors (BM25)
        current_docs = bm25_service._tenant_indices.get(tenant_id_str, {}).get("docs", [])
        bm25_service.update_tenant_index(tenant_id_str, current_docs + bm25_payloads)
        
        doc.status = "indexed"
        await db.commit()
        return doc.id
    except Exception as e:
        await db.rollback()
        try:
            doc = Document(tenant_id=tenant_uuid, filename=filename, status=f"failed: {str(e)}")
            db.add(doc)
            await db.commit()
        except Exception:
            await db.rollback()
        return None
