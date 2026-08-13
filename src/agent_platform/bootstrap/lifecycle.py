from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from agent_platform.config.settings import DatabaseSettings
from agent_platform.persistence.database import DatabaseRuntime, create_database_runtime


@asynccontextmanager
async def database_lifespan(settings: DatabaseSettings) -> AsyncIterator[DatabaseRuntime]:
    """Verify and own a role's database runtime for its complete lifetime."""

    runtime = create_database_runtime(settings)
    try:
        await runtime.check_connection()
        yield runtime
    finally:
        await runtime.dispose()
