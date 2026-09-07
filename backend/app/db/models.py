import uuid
from typing import Optional, Dict, Any
from sqlalchemy import String, Text, JSON, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base, TenantMixin, TimestampMixin

# Re-export core relational models
from app.models.tenant import Tenant
from app.models.project import Project
from app.models.document import Document, DocumentChunk, BusinessDocument

class GeneratedDoc(Base, TimestampMixin):
    """Persisted synthesized documentation for legacy functions and modules."""
    __tablename__ = "generated_docs"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    function_name: Mapped[str] = mapped_column(String(255), nullable=False)
    markdown_content: Mapped[str] = mapped_column(Text, nullable=False)

__all__ = [
    "Tenant",
    "Project",
    "Document",
    "DocumentChunk",
    "BusinessDocument",
    "GeneratedDoc",
]
