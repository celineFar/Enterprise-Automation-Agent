from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from agent_platform.config.settings import DatabaseSettings


@dataclass(frozen=True, slots=True)
class DatabaseRuntime:
    """Database resources owned by one application process."""

    engine: AsyncEngine
    sessions: async_sessionmaker[AsyncSession]

    async def check_connection(self) -> None:
        """Raise when PostgreSQL cannot execute a minimal query."""

        async with self.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

    async def dispose(self) -> None:
        """Close pooled connections owned by this runtime."""

        await self.engine.dispose()


def create_database_runtime(settings: DatabaseSettings) -> DatabaseRuntime:
    """Create an async engine and session factory without opening a connection."""

    engine = create_async_engine(
        settings.url.get_secret_value(),
        pool_size=settings.pool_size,
        max_overflow=settings.max_overflow,
        pool_timeout=settings.pool_timeout_seconds,
        pool_pre_ping=True,
        hide_parameters=True,
    )
    sessions = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autoflush=False,
        expire_on_commit=False,
    )
    return DatabaseRuntime(engine=engine, sessions=sessions)
