import psycopg
import pytest
from alembic import command
from alembic.config import Config


@pytest.mark.integration
def test_baseline_migration_up_down_and_up_again(
    postgres_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AGENT_DATABASE__URL", postgres_url)
    config = Config("alembic.ini")

    command.upgrade(config, "head")
    assert current_revision(postgres_url) == "0001_initial_schema_baseline"

    command.downgrade(config, "base")
    assert current_revision(postgres_url) is None

    command.upgrade(config, "head")
    assert current_revision(postgres_url) == "0001_initial_schema_baseline"


def current_revision(database_url: str) -> str | None:
    sync_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    with psycopg.connect(sync_url) as connection, connection.cursor() as cursor:
        cursor.execute("SELECT version_num FROM alembic_version")
        row = cursor.fetchone()
    return None if row is None else row[0]
