"""Tenant Isolation Guard and Scoping Utilities.

Enforces strict tenant boundaries at the database layer. Under NO circumstance
should any query execute without validating and filtering by the target tenant_id.
"""
from typing import Any, Type, TypeVar
from sqlalchemy import Select, select
from sqlalchemy.sql.elements import BinaryExpression

T = TypeVar("T")

class TenantIsolationError(ValueError):
    """Raised when an operation violates multi-tenant isolation constraints."""
    pass

def validate_tenant_id(tenant_id: Any) -> str:
    """Validates that tenant_id is provided, non-empty, and valid."""
    if tenant_id is None:
        raise TenantIsolationError("Security Alert: tenant_id must not be None.")
    tenant_str = str(tenant_id).strip()
    if not tenant_str:
        raise TenantIsolationError("Security Alert: tenant_id must not be empty.")
    return tenant_str

def tenant_filter(model: Type[T], tenant_id: str) -> BinaryExpression:
    """Generates a mandatory SQLAlchemy binary expression filtering by tenant_id."""
    clean_tenant_id = validate_tenant_id(tenant_id)
    if not hasattr(model, "tenant_id"):
        raise TenantIsolationError(f"Model '{model.__name__}' does not have a 'tenant_id' column.")
    return model.tenant_id == clean_tenant_id

def tenant_select(model: Type[T], tenant_id: str) -> Select:
    """Builds a SELECT statement strictly scoped to the specified tenant_id."""
    return select(model).where(tenant_filter(model, tenant_id))
