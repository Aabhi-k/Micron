import uuid
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant

class BusinessDocument(Base, TimestampMixin):
    """Business Process Document (BPD) tied strictly to a specific tenant."""
    __tablename__ = "business_documents"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    project_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    meta_info: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="documents")

    def __repr__(self) -> str:
        return f"<BusinessDocument id={self.id!r} tenant_id={self.tenant_id!r} title={self.title!r}>"
