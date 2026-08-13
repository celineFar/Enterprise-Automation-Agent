import asyncio

import pytest
from pydantic import SecretStr
from sqlalchemy import event, text

import agent_platform.bootstrap.lifecycle as lifecycle_module
from agent_platform.bootstrap.lifecycle import database_lifespan
from agent_platform.config.settings import DatabaseSettings
from agent_platform.persistence.database import create_database_runtime


@pytest.mark.integration
def test_engine_connectivity_and_async_session(postgres_url: str) -> None:
    settings = DatabaseSettings(url=SecretStr(postgres_url))
    runtime = create_database_runtime(settings)

    async def scenario() -> None:
        await runtime.check_connection()

        async with runtime.sessions() as session:
            result = await session.execute(text("SELECT 42"))
            assert result.scalar_one() == 42
            await session.commit()

        await runtime.dispose()

    asyncio.run(scenario())


@pytest.mark.integration
def test_database_lifespan_closes_pooled_connections(
    postgres_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = DatabaseSettings(url=SecretStr(postgres_url))
    runtime = create_database_runtime(settings)
    closed_connections = 0

    def record_close(_connection: object, _record: object) -> None:
        nonlocal closed_connections
        closed_connections += 1

    event.listen(runtime.engine.sync_engine, "close", record_close)

    async def scenario() -> None:
        async with database_lifespan(settings) as active_runtime:
            # Exercise this specific runtime so disposal has a pooled connection to close.
            await active_runtime.check_connection()

    monkeypatch.setattr(lifecycle_module, "create_database_runtime", lambda _settings: runtime)
    asyncio.run(scenario())

    assert closed_connections >= 1
