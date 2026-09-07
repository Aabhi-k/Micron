from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.document import BusinessDocument
    from app.models.project import Project

class Tenant(Base, TimestampMixin):
    """Tenant entity for multi-tenant isolation."""
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    documents: Mapped[List["BusinessDocument"]] = relationship(
        "BusinessDocument",
        back_populates="tenant",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    projects: Mapped[List["Project"]] = relationship(
        "Project",
        back_populates="tenant",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Tenant id={self.id!r} name={self.name!r}>"
