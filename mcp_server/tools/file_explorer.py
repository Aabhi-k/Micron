import logging
from typing import Dict, Any
from mcp_server.security import (
    validate_and_resolve_path,
    validate_file_type_and_size,
    SecurityError,
)
from mcp_server.config import STORAGE_PROJECTS_ROOT, MAX_FILE_SIZE_BYTES
from mcp_server.redaction import redact_code

logger = logging.getLogger("mcp_server.tools.file_explorer")


def execute_read_file(file_path: str) -> Dict[str, Any]:
    """
    Executes a secure read operation on a requested file within the legacy codebase sandbox.

    Workflow:
    1. Validate path and resolve sandbox boundary.
    2. Check file existence.
    3. Validate regular file type, allowed/blocked extensions, binary sniffing, and file size limits.
    4. Read file content safely with fallback encoding.
    5. In-flight secret redaction (passwords, API keys, database URIs, private IPs, tokens).
    6. Return standardized dictionary response.
    """
    try:
        # Step 1: Security path resolution
        target_path = validate_and_resolve_path(file_path, STORAGE_PROJECTS_ROOT)

        # Step 2: Check existence
        if not target_path.exists():
            logger.warning(f"File not found requested: '{file_path}'")
            return {
                "status": "error",
                "file_path": file_path,
                "sanitized_code": "",
                "redactions_applied": [],
                "size_bytes": 0,
                "error_message": f"File not found: '{file_path}'"
            }

        # Step 3: Enforce strict file type, extension, binary sniffing, and size protection
        file_size = validate_file_type_and_size(target_path, max_size_bytes=MAX_FILE_SIZE_BYTES)

        # Step 4: Read content with robust encoding handling
        try:
            raw_content = target_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raw_content = target_path.read_text(encoding="latin-1", errors="replace")

        # Step 5: Apply in-flight secret redaction before leaving the MCP boundary
        sanitized_content, redactions = redact_code(raw_content)

        # Compute safe relative path inside sandbox
        rel_path = str(target_path.relative_to(STORAGE_PROJECTS_ROOT)).replace("\\", "/")

        if redactions:
            logger.info(
                f"Successfully read '{rel_path}' ({file_size} bytes) with redactions applied: {redactions}"
            )
        else:
            logger.info(f"Successfully read '{rel_path}' ({file_size} bytes)")

        return {
            "status": "success",
            "file_path": rel_path,
            "sanitized_code": sanitized_content,
            "redactions_applied": redactions,
            "size_bytes": file_size,
            "error_message": None
        }

    except SecurityError as e:
        logger.warning(f"Security violation caught: {e}")
        return {
            "status": "error",
            "file_path": file_path,
            "sanitized_code": "",
            "redactions_applied": [],
            "size_bytes": 0,
            "error_message": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error reading file '{file_path}': {e}")
        return {
            "status": "error",
            "file_path": file_path,
            "sanitized_code": "",
            "redactions_applied": [],
            "size_bytes": 0,
            "error_message": f"Internal error reading file: {str(e)}"
        }
import os
from pathlib import Path
from typing import List, Dict, Any

def get_project_root(project_id: str, storage_base: Path) -> Path:
    """Resolve and enforce sandbox boundaries for a specific project."""
    # Check if a dedicated 'source' directory exists, otherwise use project root
    project_base = (storage_base / project_id).resolve()
    if not str(project_base).startswith(str(storage_base)):
        raise ValueError(f"Invalid or unauthorized project ID: {project_id}")

    project_source = (project_base / "source").resolve()
    if project_source.exists() and str(project_source).startswith(str(storage_base)):
        return project_source

    if not project_base.exists():
        raise ValueError(f"Project not found: {project_id}")
    return project_base

def resolve_safe_path(project_id: str, relative_path: str, storage_base: Path) -> Path:
    """Ensure relative path does not escape the project's source root."""
    root = get_project_root(project_id, storage_base)
    target = (root / relative_path.lstrip("/\\")).resolve()
    if not str(target).startswith(str(root)):
        raise PermissionError(f"Security Alert: Directory traversal detected: {relative_path}")
    return target

def safe_list_project_files(project_id: str, sub_dir: str, storage_base: Path) -> List[Dict[str, Any]]:
    """Generates the hierarchical file structure for the UI file tree."""
    target_dir = resolve_safe_path(project_id, sub_dir, storage_base)
    root = get_project_root(project_id, storage_base)
    entries = []

    if not target_dir.exists() or not target_dir.is_dir():
        return entries

    for item in sorted(target_dir.iterdir()):
        if item.name.startswith((".", "node_modules", "target", "build", "__pycache__")):
            continue
        rel_path = str(item.relative_to(root)).replace("\\", "/")
        entries.append({
            "name": item.name,
            "path": rel_path,
            "type": "directory" if item.is_dir() else "file",
            "size": item.stat().st_size if item.is_file() else 0
        })
    return entries
