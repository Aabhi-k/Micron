import os
import shutil
import zipfile
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from app.core.config import settings
from app.core.security import get_project_root

logger = logging.getLogger("backend.api.v1.projects")
router = APIRouter()

class GitCloneRequest(BaseModel):
    project_id: str
    git_url: str
    branch: Optional[str] = "main"

@router.get("/", response_model=List[Dict[str, Any]])
async def list_projects():
    """Lists all target legacy codebases currently residing in storage."""
    base = settings.STORAGE_BASE.resolve()
    base.mkdir(parents=True, exist_ok=True)
    projects = []

    for item in sorted(base.iterdir()):
        if item.is_dir() and not item.name.startswith("."):
            source_dir = item / "source"
            active_dir = source_dir if source_dir.exists() else item
            file_count = sum(1 for _ in active_dir.rglob("*") if _.is_file())
            projects.append({
                "project_id": item.name,
                "name": item.name,
                "path": str(item),
                "file_count": file_count
            })

    return projects

@router.get("/{project_id}")
async def get_project(project_id: str):
    """Retrieves metadata and status of a specific target codebase."""
    root = get_project_root(project_id)
    file_count = sum(1 for _ in root.rglob("*") if _.is_file())
    return {
        "project_id": project_id,
        "root_path": str(root),
        "file_count": file_count
    }

@router.post("/upload")
async def upload_project(
    project_id: str = Form(...),
    file: UploadFile = File(...)
):
    """Uploads and unpacks a zip archive of legacy code into the project sandbox."""
    base = settings.STORAGE_BASE.resolve()
    target_dir = base / project_id / "source"
    target_dir.mkdir(parents=True, exist_ok=True)

    zip_path = base / f"{project_id}_temp.zip"
    try:
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Check for path traversal in zip
            for member in zip_ref.namelist():
                if member.startswith("/") or ".." in member:
                    raise HTTPException(status_code=400, detail="Malicious zip contents detected.")
            zip_ref.extractall(target_dir)

        return {"status": "success", "project_id": project_id, "message": "Project uploaded and unpacked."}
    finally:
        if zip_path.exists():
            zip_path.unlink()

@router.post("/clone")
async def clone_project(req: GitCloneRequest):
    """Clones a remote git repository into the project sandbox."""
    import subprocess
    base = settings.STORAGE_BASE.resolve()
    target_dir = base / req.project_id / "source"

    if target_dir.exists():
        raise HTTPException(status_code=400, detail="Project already exists.")

    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        cmd = ["git", "clone", "--depth", "1"]
        if req.branch:
            cmd.extend(["-b", req.branch])
        cmd.extend([req.git_url, str(target_dir)])

        process = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return {
            "status": "success", 
            "project_id": req.project_id, 
            "message": "Project cloned successfully."
        }
    except subprocess.CalledProcessError as e:
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Git clone failed: {e.stderr}")
