from pathlib import Path
from typing import Optional
from fastapi import HTTPException
from app.core.config import settings

def get_project_root(project_id: str) -> Path:
    """Resolve and enforce sandbox boundaries for a specific project."""
    base = settings.STORAGE_BASE.resolve()
    project_dir = (base / project_id).resolve()
    
    if not str(project_dir).startswith(str(base)):
        raise HTTPException(status_code=400, detail="Invalid project identifier.")

    source_dir = (project_dir / "source").resolve()
    if source_dir.exists() and str(source_dir).startswith(str(base)):
        return source_dir

    if not project_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    return project_dir

def validate_safe_path(project_id: str, relative_path: str = "") -> Path:
    """Ensure relative path does not escape the project root."""
    root = get_project_root(project_id)
    target = (root / relative_path.lstrip("/\\")).resolve()
    
    if not str(target).startswith(str(root)):
        raise HTTPException(
            status_code=403, 
            detail=f"Security Alert: Path traversal attempt detected: {relative_path}"
        )
    return target

def validate_tenant_id(tenant_id: Optional[str]) -> str:
    """Strictly validates tenant_id to prevent multi-tenant data leakage.
    Raises HTTPException(400) or ValueError if tenant_id is missing or malformed.
    """
    if not tenant_id or not str(tenant_id).strip():
        raise HTTPException(
            status_code=400,
            detail="Security Violation: A valid tenant_id is strictly required for this operation."
        )
    cleaned = str(tenant_id).strip()
    if "/" in cleaned or "\\" in cleaned or ".." in cleaned:
        raise HTTPException(
            status_code=400,
            detail="Security Violation: Malformed tenant_id detected."
        )
    return cleaned

