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
