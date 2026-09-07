from fastapi import APIRouter, File, UploadFile, Header, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.ingestion.indexer import process_and_index_document

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...), 
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"), 
    db: AsyncSession = Depends(get_db)
):
    if not x_tenant_id or not x_tenant_id.strip():
        raise HTTPException(status_code=400, detail="X-Tenant-ID is required")
        
    content = await file.read()
    
    doc_id = await process_and_index_document(content, file.filename, x_tenant_id, db)
    
    return {"document_id": str(doc_id) if doc_id else "", "status": "indexed" if doc_id else "failed", "filename": file.filename}
