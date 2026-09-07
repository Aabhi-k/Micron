import json
import logging
import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.security import validate_safe_path
from app.services.mcp_client import call_mcp_tool
from app.db.session import get_db
from app.models.project import Project

logger = logging.getLogger("backend.api.v1.files")
router = APIRouter()


def _parse_tenant_uuid(x_tenant_id: str) -> uuid.UUID:
    if not x_tenant_id or not x_tenant_id.strip():
        raise HTTPException(status_code=400, detail="X-Tenant-ID header is required.")
    try:
        return uuid.UUID(x_tenant_id)
    except (ValueError, AttributeError):
        return uuid.uuid5(uuid.NAMESPACE_DNS, x_tenant_id)


async def _verify_project_ownership(project_id: str, x_tenant_id: Optional[str], db: AsyncSession):
    if not x_tenant_id:
        return
    tenant_uuid = _parse_tenant_uuid(x_tenant_id)
    default_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")
    query = select(Project).where(Project.id == project_id)
    res = await db.execute(query)
    proj = res.scalars().first()
    if proj:
        if proj.tenant_id != tenant_uuid:
            raise HTTPException(status_code=403, detail=f"Access Denied: Project '{project_id}' does not belong to requesting tenant.")
    else:
        if not (tenant_uuid == default_uuid and project_id == "passman-main"):
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found for requesting tenant.")


@router.get("/tree/{project_id}")
async def get_file_tree(
    project_id: str,
    sub_dir: str = Query("", description="Relative subdirectory inside project"),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    db: AsyncSession = Depends(get_db)
):
    """Generates the hierarchical file structure for the UI file tree using MCP."""
    await _verify_project_ownership(project_id, x_tenant_id, db)
    try:
        raw_res = await call_mcp_tool("list_project_files", {
            "project_id": project_id,
            "sub_dir": sub_dir
        })
        files = json.loads(raw_res) if isinstance(raw_res, str) else raw_res
        return {"project_id": project_id, "sub_dir": sub_dir, "files": files}
    except Exception as e:
        logger.error(f"Error listing project files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content/{project_id}")
async def get_file_content(
    project_id: str,
    path: str = Query(..., description="Relative file path"),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves file content safely within the sandboxed project repository."""
    await _verify_project_ownership(project_id, x_tenant_id, db)
    file_path = validate_safe_path(project_id, path)

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        return {
            "project_id": project_id,
            "path": path,
            "size": file_path.stat().st_size,
            "content": content
        }
    except Exception as e:
        logger.error(f"Failed to read file {path}: {e}")
        raise HTTPException(status_code=500, detail="Error reading file content.")

