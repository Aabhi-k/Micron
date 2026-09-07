import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from app.core.security import validate_safe_path
from app.services.mcp_client import call_mcp_tool

logger = logging.getLogger("backend.api.v1.files")
router = APIRouter()

@router.get("/tree/{project_id}")
async def get_file_tree(project_id: str, sub_dir: str = Query("", description="Relative subdirectory inside project")):
    """Generates the hierarchical file structure for the UI file tree using MCP."""
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
async def get_file_content(project_id: str, path: str = Query(..., description="Relative file path")):
    """Retrieves file content safely within the sandboxed project repository."""
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
