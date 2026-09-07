from pathlib import Path
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
