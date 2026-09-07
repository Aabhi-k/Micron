import json
import logging
import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.mcp_client import call_mcp_tool
from app.db.session import get_db
from app.models.project import Project
from app.core.observability import observe, trace_tenant_context

logger = logging.getLogger("backend.api.v1.symbols")
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


@router.get("/ast")
@observe(name="get_symbol_ast", as_type="tool")
async def get_symbol_ast(
    project_id: str = Query(..., description="Target project identifier"),
    file_path: str = Query(..., description="Relative file path"),
    function_name: str = Query(..., description="Function or symbol name to extract"),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    db: AsyncSession = Depends(get_db)
):
    """Extracts exact function code, byte offsets, and AST definition via MCP."""
    await _verify_project_ownership(project_id, x_tenant_id, db)
    try:
        with trace_tenant_context(tenant_id=x_tenant_id, project_id=project_id):
            raw_res = await call_mcp_tool("get_function_ast", {
                "project_id": project_id,
                "file_path": file_path,
                "function_name": function_name
            })
            data = json.loads(raw_res) if isinstance(raw_res, str) else raw_res
            if not data.get("found"):
                raise HTTPException(status_code=404, detail=data.get("message", "Symbol not found"))
            return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching symbol AST: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dependencies")
@observe(name="get_symbol_dependencies", as_type="tool")
async def get_symbol_dependencies(
    project_id: str = Query(..., description="Target project identifier"),
    file_path: str = Query(..., description="Relative file path"),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves file imports, includes, and symbol dependency references."""
    await _verify_project_ownership(project_id, x_tenant_id, db)
    try:
        with trace_tenant_context(tenant_id=x_tenant_id, project_id=project_id):
            raw_res = await call_mcp_tool("get_dependencies", {
                "project_id": project_id,
                "file_path": file_path
            })
            return json.loads(raw_res) if isinstance(raw_res, str) else raw_res
    except Exception as e:
        logger.error(f"Error fetching dependencies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

