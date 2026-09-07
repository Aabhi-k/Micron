from app.db.base import Base, TenantMixin, TimestampMixin
from app.db.session import get_db, init_db, AsyncSessionLocal, engine
from app.db.tenant_guard import (
    TenantIsolationError,
    validate_tenant_id,
    tenant_filter,
    tenant_select,
)

__all__ = [
    "Base",
    "TenantMixin",
    "TimestampMixin",
    "get_db",
    "init_db",
    "AsyncSessionLocal",
    "engine",
    "TenantIsolationError",
    "validate_tenant_id",
    "tenant_filter",
    "tenant_select",
]

def __getattr__(name: str):
    if name in ("Tenant", "Project", "BusinessDocument", "Document", "DocumentChunk", "GeneratedDoc"):
        from app.db import models
        return getattr(models, name)
    if name in ("TenantRepository", "ProjectRepository", "BusinessDocumentRepository", "GeneratedDocRepository"):
        from app.db import repository
        return getattr(repository, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
