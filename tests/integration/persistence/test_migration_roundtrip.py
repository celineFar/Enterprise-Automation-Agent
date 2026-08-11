import os

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from docker.errors import DockerException  # type: ignore[import-untyped]
from testcontainers.community.postgres import PostgresContainer


@pytest.mark.integration
def test_baseline_migration_up_down_and_up_again(monkeypatch: pytest.MonkeyPatch) -> None:
    try:
        postgres = PostgresContainer("postgres:17.6-bookworm", driver="psycopg")
        postgres.start()
    except DockerException as error:
        pytest.skip(f"Docker is unavailable: {error}")

    try:
        database_url = postgres.get_connection_url()
        monkeypatch.setenv("AGENT_DATABASE__URL", database_url)
        config = Config("alembic.ini")

        command.upgrade(config, "head")
        assert current_revision(database_url) == "0001_initial_schema_baseline"

        command.downgrade(config, "base")
        assert current_revision(database_url) is None

        command.upgrade(config, "head")
        assert current_revision(database_url) == "0001_initial_schema_baseline"
    finally:
        postgres.stop()
        os.environ.pop("AGENT_DATABASE__URL", None)


def current_revision(database_url: str) -> str | None:
    sync_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    with psycopg.connect(sync_url) as connection, connection.cursor() as cursor:
        cursor.execute("SELECT version_num FROM alembic_version")
        row = cursor.fetchone()
    return None if row is None else row[0]
