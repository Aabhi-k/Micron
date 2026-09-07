import json
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Query
from app.services.mcp_client import call_mcp_tool

logger = logging.getLogger("backend.api.v1.symbols")
router = APIRouter()

@router.get("/ast")
async def get_symbol_ast(
    project_id: str = Query(..., description="Target project identifier"),
    file_path: str = Query(..., description="Relative file path"),
    function_name: str = Query(..., description="Function or symbol name to extract")
):
    """Extracts exact function code, byte offsets, and AST definition via MCP."""
    try:
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
async def get_symbol_dependencies(
    project_id: str = Query(..., description="Target project identifier"),
    file_path: str = Query(..., description="Relative file path")
):
    """Retrieves file imports, includes, and symbol dependency references."""
    try:
        raw_res = await call_mcp_tool("get_dependencies", {
            "project_id": project_id,
            "file_path": file_path
        })
        return json.loads(raw_res) if isinstance(raw_res, str) else raw_res
    except Exception as e:
        logger.error(f"Error fetching dependencies: {e}")
        raise HTTPException(status_code=500, detail=str(e))
