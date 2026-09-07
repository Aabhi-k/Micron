import os
import logging
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
from app.core.config import settings

logger = logging.getLogger("backend.core.observability")

# Sync settings into environment for Langfuse automatic client initialization
if settings.LANGFUSE_PUBLIC_KEY and not os.getenv("LANGFUSE_PUBLIC_KEY"):
    os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
if settings.LANGFUSE_SECRET_KEY and not os.getenv("LANGFUSE_SECRET_KEY"):
    os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
if settings.LANGFUSE_HOST and not os.getenv("LANGFUSE_HOST"):
    os.environ["LANGFUSE_HOST"] = settings.LANGFUSE_HOST

try:
    from langfuse import observe, propagate_attributes, Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError as err:
    logger.warning(f"Langfuse not available: {err}. Tracing will be disabled.")
    LANGFUSE_AVAILABLE = False

    # Safe fallback no-op decorators
    def observe(*args, **kwargs):
        def decorator(fn):
            return fn
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator

    @contextmanager
    def propagate_attributes(**kwargs):
        yield

    class Langfuse:
        def __init__(self, *args, **kwargs):
            pass


@contextmanager
def trace_tenant_context(
    tenant_id: Optional[str] = None,
    project_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Context manager to inject tenant and project isolation attributes into the active Langfuse trace.
    Sets user_id = tenant_id and tags = [project_id].
    """
    applied_tags = list(tags or [])
    if project_id and project_id not in applied_tags:
        applied_tags.append(str(project_id))

    meta = dict(metadata or {})
    if tenant_id:
        meta["tenant_id"] = str(tenant_id)
    if project_id:
        meta["project_id"] = str(project_id)

    with propagate_attributes(
        user_id=str(tenant_id) if tenant_id else None,
        tags=applied_tags,
        metadata=meta
    ):
        yield
