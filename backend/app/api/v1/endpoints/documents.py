import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, File, UploadFile, Header, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.document import Document, DocumentChunk
from app.services.ingestion.indexer import process_and_index_document

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...), 
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"), 
    db: AsyncSession = Depends(get_db)
):
    """Uploads and indexes any document (PDF, TXT, MD) under the specified tenant."""
    if not x_tenant_id or not x_tenant_id.strip():
        raise HTTPException(status_code=400, detail="X-Tenant-ID is required")

    content = await file.read()
    doc_id = await process_and_index_document(content, file.filename, x_tenant_id, db)

    return {
        "document_id": str(doc_id) if doc_id else "",
        "status": "indexed" if doc_id else "failed",
        "filename": file.filename
    }


@router.get("/", response_model=List[Dict[str, Any]])
async def list_documents(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    db: AsyncSession = Depends(get_db)
):
    """Lists all ingested business process documents strictly scoped to the requesting tenant."""
    if not x_tenant_id or not x_tenant_id.strip():
        raise HTTPException(status_code=400, detail="X-Tenant-ID is required")

    try:
        tenant_uuid = uuid.UUID(x_tenant_id)
    except (ValueError, AttributeError):
        tenant_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, x_tenant_id)

    query = select(Document).where(Document.tenant_id == tenant_uuid).order_by(Document.created_at.desc())
    res = await db.execute(query)
    docs = res.scalars().all()

    return [
        {
            "id": str(d.id),
            "tenant_id": str(d.tenant_id),
            "filename": d.filename,
            "status": d.status,
            "created_at": d.created_at.isoformat() if d.created_at else None
        }
        for d in docs
    ]


@router.get("/{document_id}/chunks", response_model=List[Dict[str, Any]])
async def get_document_chunks(
    document_id: str,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves all indexed text chunks belonging to a specific document."""
    if not x_tenant_id or not x_tenant_id.strip():
        raise HTTPException(status_code=400, detail="X-Tenant-ID is required")

    try:
        doc_uuid = uuid.UUID(document_id)
        tenant_uuid = uuid.UUID(x_tenant_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    query = select(DocumentChunk).where(
        DocumentChunk.document_id == doc_uuid,
        DocumentChunk.tenant_id == tenant_uuid
    ).order_by(DocumentChunk.chunk_index.asc())

    res = await db.execute(query)
    chunks = res.scalars().all()

    return [
        {
            "id": str(c.id),
            "document_id": str(c.document_id),
            "chunk_index": c.chunk_index,
            "content": c.content,
        }
        for c in chunks
    ]
