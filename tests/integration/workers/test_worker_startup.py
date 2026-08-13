import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from sqlalchemy import event

from agent_platform.bootstrap.lifecycle import database_lifespan as original_database_lifespan
from agent_platform.config.settings import DatabaseSettings, WorkerSettings
from agent_platform.persistence.database import DatabaseRuntime
from agent_platform.workers import main as worker_main


@pytest.mark.integration
def test_worker_initializes_postgres_and_disposes_engine(
    worker_settings: WorkerSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connected = asyncio.Event()
    closed_connections = 0

    @asynccontextmanager
    async def observed_lifespan(
        settings: DatabaseSettings,
    ) -> AsyncIterator[DatabaseRuntime]:
        nonlocal closed_connections
        async with original_database_lifespan(settings) as database:
            event.listen(
                database.engine.sync_engine,
                "close",
                lambda _connection, _record: record_close(),
            )
            await database.check_connection()
            connected.set()
            yield database

    def record_close() -> None:
        nonlocal closed_connections
        closed_connections += 1

    monkeypatch.setattr(worker_main, "database_lifespan", observed_lifespan)

    async def scenario() -> None:
        stop_event = asyncio.Event()
        worker = asyncio.create_task(
            worker_main.run_worker(
                worker_settings,
                stop_event,
                register_signals=False,
            )
        )
        await asyncio.wait_for(connected.wait(), timeout=10)
        assert not worker.done()

        stop_event.set()
        await asyncio.wait_for(worker, timeout=10)

    asyncio.run(scenario())
    assert closed_connections >= 1
