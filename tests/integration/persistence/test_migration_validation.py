import pytest
from alembic import command
from scripts.check_migrations import alembic_config, validate_migrations


@pytest.mark.integration
def test_shared_migration_validator_against_disposable_postgres(postgres_url: str) -> None:
    # The validator deliberately requires an empty database as a safety boundary.
    command.downgrade(alembic_config(postgres_url), "base")

    output: list[str] = []
    validate_migrations(postgres_url, output=output.append)

    assert "Migration upgrade to head succeeded" in output
    assert "Migration downgrade to base succeeded" in output
    assert "Migration re-upgrade to head succeeded" in output
    assert "No uncommitted SQLAlchemy metadata changes detected" in output
