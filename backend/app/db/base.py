from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs

class Base(AsyncAttrs, DeclarativeBase):
    """Base declarative class with async attribute support."""
    pass

class TenantMixin:
    """Enforces strict tenant scoping and indexing on tenant-aware database models."""
    tenant_id: Mapped[str] = mapped_column(
        String(64), 
        nullable=False, 
        index=True,
        doc="Tenant unique identifier for strict multi-tenant isolation"
    )

class TimestampMixin:
    """Provides created_at and updated_at timestamps in UTC."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
