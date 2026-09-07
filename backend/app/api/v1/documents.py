import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.tenant_guard import validate_tenant_id, tenant_select, TenantIsolationError
from app.models.document import BusinessDocument
from app.models.tenant import Tenant
from app.services.rag_engine import index_business_document, search_business_docs

logger = logging.getLogger("backend.api.v1.documents")
router = APIRouter()

class DocumentCreateRequest(BaseModel):
    tenant_id: Optional[str] = None
    project_id: Optional[str] = None
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    meta_info: Dict[str, Any] = Field(default_factory=dict)

class DocumentSearchRequest(BaseModel):
    tenant_id: Optional[str] = None
    query: str = Field(..., min_length=1)
    project_id: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=50)

def resolve_tenant_id(body_tenant: Optional[str], header_tenant: Optional[str]) -> str:
    """Extracts and enforces non-empty tenant_id from body or X-Tenant-ID header."""
    candidate = body_tenant or header_tenant
    if not candidate or not str(candidate).strip():
        raise HTTPException(
            status_code=400,
            detail="Tenant Isolation Policy: 'tenant_id' must be provided in the payload or 'X-Tenant-ID' header."
        )
    return validate_tenant_id(candidate)

@router.post("/", response_model=Dict[str, Any])
async def create_document(
    req: DocumentCreateRequest,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    db: AsyncSession = Depends(get_db)
):
    """Ingests and indexes a Business Process Document for a specific tenant."""
    tenant_id = resolve_tenant_id(req.tenant_id, x_tenant_id)

    # Ensure tenant exists in DB
    tenant_stmt = select(Tenant).where(Tenant.id == tenant_id)
    tenant_res = await db.execute(tenant_stmt)
    tenant = tenant_res.scalar_one_or_none()
    if not tenant:
        tenant = Tenant(id=tenant_id, name=f"Tenant {tenant_id}")
        db.add(tenant)
        await db.flush()

    res = await index_business_document(
        tenant_id=tenant_id,
        title=req.title,
        content=req.content,
        project_id=req.project_id,
        metadata=req.meta_info,
        session=db
    )
    return {
        "status": "success",
        "document": res
    }

@router.get("/", response_model=List[Dict[str, Any]])
async def list_documents(
    tenant_id: Optional[str] = Query(None),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    project_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Lists all business documents belonging exclusively to the target tenant."""
    clean_tenant_id = resolve_tenant_id(tenant_id, x_tenant_id)

    stmt = tenant_select(BusinessDocument, clean_tenant_id)
    if project_id:
        stmt = stmt.where(BusinessDocument.project_id == project_id)

    res = await db.execute(stmt)
    docs = res.scalars().all()

    return [
        {
            "id": d.id,
            "tenant_id": d.tenant_id,
            "project_id": d.project_id,
            "title": d.title,
            "content": d.content,
            "meta_info": d.meta_info,
            "created_at": d.created_at.isoformat() if d.created_at else None
        }
        for d in docs
    ]

@router.post("/search", response_model=List[Dict[str, Any]])
async def search_documents(
    req: DocumentSearchRequest,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
):
    """Performs isolated hybrid RAG search (Dense + BM25 + RRF + Cross-Encoder) for a tenant."""
    tenant_id = resolve_tenant_id(req.tenant_id, x_tenant_id)

    results = await search_business_docs(
        tenant_id=tenant_id,
        query=req.query,
        project_id=req.project_id,
        top_k=req.top_k
    )
    return results
