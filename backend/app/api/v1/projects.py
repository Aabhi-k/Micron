import os
import uuid
import shutil
import zipfile
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.core.config import settings
from app.core.security import get_project_root
from app.db.session import get_db
from app.models.project import Project
from app.models.tenant import Tenant

logger = logging.getLogger("backend.api.v1.projects")
router = APIRouter()


class GitCloneRequest(BaseModel):
    project_id: str
    git_url: str
    branch: Optional[str] = "main"


def _parse_tenant_uuid(x_tenant_id: str) -> uuid.UUID:
    if not x_tenant_id or not x_tenant_id.strip():
        raise HTTPException(status_code=400, detail="X-Tenant-ID header is required.")
    try:
        return uuid.UUID(x_tenant_id)
    except (ValueError, AttributeError):
        return uuid.uuid5(uuid.NAMESPACE_DNS, x_tenant_id)


@router.get("/", response_model=List[Dict[str, Any]])
async def list_projects(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    db: AsyncSession = Depends(get_db)
):
    """Lists target legacy codebases strictly belonging to the requesting tenant."""
    tenant_uuid = _parse_tenant_uuid(x_tenant_id)
    base = settings.STORAGE_BASE.resolve()
    base.mkdir(parents=True, exist_ok=True)

    # Auto-seed passman-main for default tenant if it exists on disk
    default_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")
    if tenant_uuid == default_uuid and (base / "passman-main").exists():
        pm_res = await db.execute(select(Project).where(Project.id == "passman-main"))
        if not pm_res.scalar_one_or_none():
            t_res = await db.execute(select(Tenant).where(Tenant.id == default_uuid))
            if not t_res.scalar_one_or_none():
                db.add(Tenant(id=default_uuid, name="Default Organization"))
                await db.commit()
            db.add(Project(
                id="passman-main",
                tenant_id=default_uuid,
                name="Passman Legacy Codebase",
                root_path=str(base / "passman-main")
            ))
            await db.commit()

    query = select(Project).where(Project.tenant_id == tenant_uuid).order_by(Project.created_at.desc())
    res = await db.execute(query)
    db_projects = res.scalars().all()

    projects = []
    for p in db_projects:
        try:
            root = get_project_root(p.id)
            file_count = sum(1 for _ in root.rglob("*") if _.is_file())
        except Exception:
            file_count = 0

        projects.append({
            "project_id": p.id,
            "name": p.name,
            "path": p.root_path or str(base / p.id),
            "file_count": file_count,
            "tenant_id": str(p.tenant_id)
        })

    return projects


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves metadata and status of a specific target codebase strictly scoped to the requesting tenant."""
    tenant_uuid = _parse_tenant_uuid(x_tenant_id)

    query = select(Project).where(Project.id == project_id, Project.tenant_id == tenant_uuid)
    res = await db.execute(query)
    proj = res.scalars().first()

    if not proj:
        raise HTTPException(
            status_code=404, 
            detail=f"Project '{project_id}' not found or does not belong to requesting tenant."
        )

    root = get_project_root(project_id)
    file_count = sum(1 for _ in root.rglob("*") if _.is_file())
    return {
        "project_id": project_id,
        "name": proj.name,
        "tenant_id": str(proj.tenant_id),
        "root_path": str(root),
        "file_count": file_count
    }


@router.post("/upload")
async def upload_project(
    project_id: str = Form(...),
    file: UploadFile = File(...),
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    db: AsyncSession = Depends(get_db)
):
    """Uploads and unpacks a zip archive of legacy code into the project sandbox under the requesting tenant."""
    tenant_uuid = _parse_tenant_uuid(x_tenant_id)

    # Ensure tenant exists
    tenant_res = await db.execute(select(Tenant).where(Tenant.id == tenant_uuid))
    if not tenant_res.scalar_one_or_none():
        db.add(Tenant(id=tenant_uuid, name=f"Tenant {x_tenant_id}"))
        await db.commit()

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

        # Register or update project in database
        proj_res = await db.execute(select(Project).where(Project.id == project_id))
        existing_proj = proj_res.scalars().first()
        if existing_proj:
            if existing_proj.tenant_id != tenant_uuid:
                raise HTTPException(status_code=403, detail="Project ID already exists under another tenant.")
        else:
            db.add(Project(
                id=project_id,
                tenant_id=tenant_uuid,
                name=project_id,
                root_path=str(target_dir)
            ))
            await db.commit()

        return {
            "status": "success", 
            "project_id": project_id, 
            "tenant_id": str(tenant_uuid),
            "message": "Project uploaded and unpacked."
        }
    finally:
        if zip_path.exists():
            zip_path.unlink()


@router.post("/clone")
async def clone_project(
    req: GitCloneRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    db: AsyncSession = Depends(get_db)
):
    """Clones a remote git repository into the project sandbox scoped to the requesting tenant."""
    tenant_uuid = _parse_tenant_uuid(x_tenant_id)

    # Ensure tenant exists
    tenant_res = await db.execute(select(Tenant).where(Tenant.id == tenant_uuid))
    if not tenant_res.scalar_one_or_none():
        db.add(Tenant(id=tenant_uuid, name=f"Tenant {x_tenant_id}"))
        await db.commit()

    import subprocess
    base = settings.STORAGE_BASE.resolve()
    target_dir = base / req.project_id / "source"

    if target_dir.exists():
        raise HTTPException(status_code=400, detail="Project directory already exists.")

    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        cmd = ["git", "clone", "--depth", "1"]
        if req.branch:
            cmd.extend(["-b", req.branch])
        cmd.extend([req.git_url, str(target_dir)])

        subprocess.run(cmd, capture_output=True, text=True, check=True)

        db.add(Project(
            id=req.project_id,
            tenant_id=tenant_uuid,
            name=req.project_id,
            root_path=str(target_dir)
        ))
        await db.commit()

        return {
            "status": "success", 
            "project_id": req.project_id, 
            "tenant_id": str(tenant_uuid),
            "message": "Project cloned successfully."
        }
    except subprocess.CalledProcessError as e:
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Git clone failed: {e.stderr}")
