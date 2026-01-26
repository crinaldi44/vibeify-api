"""Database connection and session management."""
import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from vibeify_api.core.config import get_settings

settings = get_settings()

_engine = None
_engine_pid: int | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None
_sessionmaker_pid: int | None = None


def get_engine():
    """
    Get a process-local async engine.

    Celery uses a prefork worker model by default. If we create the engine in the
    parent process and then fork, asyncpg/SQLAlchemy pools can behave badly.
    This getter ensures each process has its own engine + pool.
    """
    global _engine, _engine_pid, _sessionmaker, _sessionmaker_pid
    pid = os.getpid()
    if _engine is None or _engine_pid != pid:
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.DEBUG,
            future=True,
        )
        _engine_pid = pid
        # Reset sessionmaker to bind to the new engine in this process.
        _sessionmaker = None
        _sessionmaker_pid = None
    return _engine


def _get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker, _sessionmaker_pid
    pid = os.getpid()
    if _sessionmaker is None or _sessionmaker_pid != pid:
        _sessionmaker = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        _sessionmaker_pid = pid
    return _sessionmaker


def AsyncSessionLocal() -> AsyncSession:
    """Backwards-compatible session factory used throughout the codebase."""
    return _get_sessionmaker()()

# Base class for models - SQLModel provides its own Base
# SQLModel's metadata is compatible with SQLAlchemy for Alembic
Base = SQLModel


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session.

    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    # SQLModel uses SQLAlchemy's metadata system
    # Import all models before calling this to register them
    async with get_engine().begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await get_engine().dispose()
