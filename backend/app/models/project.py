from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

import uuid
from sqlalchemy.dialects.postgresql import UUID

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.document import Document

class Project(Base, TimestampMixin):
    """Target codebase project belonging to a specific tenant."""
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    root_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="projects")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Project id={self.id!r} tenant_id={self.tenant_id!r} name={self.name!r}>"
