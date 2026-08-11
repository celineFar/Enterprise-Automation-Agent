import asyncio

from pydantic import SecretStr

from agent_platform.config.settings import DatabaseSettings
from agent_platform.persistence.database import create_database_runtime
from agent_platform.persistence.metadata import NAMING_CONVENTION, Base


def test_database_runtime_configures_async_sessions() -> None:
    settings = DatabaseSettings(
        url=SecretStr("postgresql+psycopg://relay:secret@localhost:5432/relay"),
        pool_size=3,
        max_overflow=2,
        pool_timeout_seconds=4,
    )

    runtime = create_database_runtime(settings)
    session = runtime.sessions()

    assert runtime.engine.url.drivername == "postgresql+psycopg"
    assert "secret" not in runtime.engine.url.render_as_string(hide_password=True)
    assert session.bind is runtime.engine
    assert session.sync_session.expire_on_commit is False

    asyncio.run(session.close())
    asyncio.run(runtime.dispose())


def test_shared_metadata_has_deterministic_naming_conventions() -> None:
    assert Base.metadata.naming_convention == NAMING_CONVENTION
    assert Base.metadata.tables == {}
