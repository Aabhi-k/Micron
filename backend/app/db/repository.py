from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import Base, TenantMixin
from app.db.models import Project, BusinessDocument, GeneratedDoc

T = TypeVar("T", bound=Base)

class TenantRepository(Generic[T]):
    """Base async repository enforcing strict tenant isolation on all operations."""

    def __init__(self, model: Type[T], session: AsyncSession, tenant_id: str):
        if not tenant_id or not str(tenant_id).strip():
            raise ValueError("tenant_id is strictly required for all repository operations.")
        self.model = model
        self.session = session
        self.tenant_id = str(tenant_id).strip()

        # Enforce that model inherits TenantMixin if scoped
        if not hasattr(model, "tenant_id"):
            raise TypeError(f"Model {model.__name__} does not have a tenant_id attribute.")

    async def get(self, item_id: str) -> Optional[T]:
        """Fetch a single record strictly scoped to this tenant."""
        stmt = (
            select(self.model)
            .where(self.model.id == item_id)
            .where(self.model.tenant_id == self.tenant_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        additional_filters: Optional[List[Any]] = None
    ) -> List[T]:
        """Fetch multiple records strictly scoped to this tenant."""
        stmt = select(self.model).where(self.model.tenant_id == self.tenant_id)
        if additional_filters:
            for flt in additional_filters:
                stmt = stmt.where(flt)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> T:
        """Create a new record, automatically setting and enforcing tenant_id."""
        kwargs["tenant_id"] = self.tenant_id
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def update(self, item_id: str, **kwargs) -> Optional[T]:
        """Update record fields strictly bounded to this tenant. tenant_id cannot be changed."""
        kwargs.pop("tenant_id", None)  # Prevent cross-tenant migration
        stmt = (
            update(self.model)
            .where(self.model.id == item_id)
            .where(self.model.tenant_id == self.tenant_id)
            .values(**kwargs)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def delete(self, item_id: str) -> bool:
        """Delete a record strictly bounded to this tenant."""
        stmt = (
            delete(self.model)
            .where(self.model.id == item_id)
            .where(self.model.tenant_id == self.tenant_id)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return (result.rowcount or 0) > 0

class ProjectRepository(TenantRepository[Project]):
    def __init__(self, session: AsyncSession, tenant_id: str):
        super().__init__(Project, session, tenant_id)

class BusinessDocumentRepository(TenantRepository[BusinessDocument]):
    def __init__(self, session: AsyncSession, tenant_id: str):
        super().__init__(BusinessDocument, session, tenant_id)

    async def list_by_project(self, project_id: str, limit: int = 100) -> List[BusinessDocument]:
        return await self.list(
            limit=limit,
            additional_filters=[BusinessDocument.project_id == project_id]
        )

class GeneratedDocRepository(TenantRepository[GeneratedDoc]):
    def __init__(self, session: AsyncSession, tenant_id: str):
        super().__init__(GeneratedDoc, session, tenant_id)
