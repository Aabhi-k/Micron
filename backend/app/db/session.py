import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine
)
from app.core.config import settings
from app.db.base import Base

logger = logging.getLogger("backend.db.session")

# Database URL normalization for asyncpg
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine: AsyncEngine = create_async_engine(
    db_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an isolated async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def init_db(custom_engine: AsyncEngine = None) -> bool:
    """Initializes schema tables asynchronously during application startup."""
    active_engine = custom_engine or engine
    logger.info("Initializing relational database schema...")
    try:
        async with active_engine.begin() as conn:
            # Import models so they are registered on Base.metadata
            import app.models  # noqa: F401
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema initialized successfully.")
        return True
    except Exception as e:
        logger.warning(
            f"Database initialization deferred: {e}. "
            "Ensure PostgreSQL container is running."
        )
        return False
