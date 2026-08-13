import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
from pydantic import SecretStr

from agent_platform.bootstrap import lifecycle
from agent_platform.config.settings import DatabaseSettings
from agent_platform.persistence.database import DatabaseRuntime


def database_settings() -> DatabaseSettings:
    return DatabaseSettings(url=SecretStr("postgresql+psycopg://relay:secret@localhost:5432/relay"))


def test_database_lifespan_checks_connection_and_disposes_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = Mock(spec=DatabaseRuntime)
    runtime.check_connection = AsyncMock()
    runtime.dispose = AsyncMock()
    monkeypatch.setattr(lifecycle, "create_database_runtime", lambda _settings: runtime)

    async def scenario() -> None:
        async with lifecycle.database_lifespan(database_settings()) as active_runtime:
            assert active_runtime is runtime
            runtime.check_connection.assert_awaited_once_with()
            runtime.dispose.assert_not_awaited()

        runtime.dispose.assert_awaited_once_with()

    asyncio.run(scenario())


def test_database_lifespan_disposes_runtime_when_connection_check_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = Mock(spec=DatabaseRuntime)
    runtime.check_connection = AsyncMock(side_effect=ConnectionError("unavailable"))
    runtime.dispose = AsyncMock()
    monkeypatch.setattr(lifecycle, "create_database_runtime", lambda _settings: runtime)

    async def scenario() -> None:
        with pytest.raises(ConnectionError, match="unavailable"):
            async with lifecycle.database_lifespan(database_settings()):
                pytest.fail("lifecycle started without PostgreSQL")

        runtime.dispose.assert_awaited_once_with()

    asyncio.run(scenario())
