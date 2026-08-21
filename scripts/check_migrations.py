import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, pool

from agent_platform.config.settings import MigrationSettings
from agent_platform.persistence.metadata import Base

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class MigrationValidationError(RuntimeError):
    """A safe-to-display migration validation failure."""


def alembic_config(database_url: str) -> Config:
    """Create Alembic configuration without writing the secret URL to disk."""

    config = Config(PROJECT_ROOT / "alembic.ini")
    config.attributes["database_url"] = database_url
    return config


def require_single_head(config: Config) -> str:
    """Return the sole migration head or fail on an empty/divergent graph."""

    heads = ScriptDirectory.from_config(config).get_heads()
    if len(heads) != 1:
        message = f"expected exactly one Alembic head, found {len(heads)}"
        raise MigrationValidationError(message)
    return heads[0]


def current_revisions(database_url: str) -> tuple[str, ...]:
    """Read applied revisions without retaining a pooled connection."""

    engine = create_engine(
        database_url,
        hide_parameters=True,
        poolclass=pool.NullPool,
    )
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            return tuple(context.get_current_heads())
    finally:
        engine.dispose()


def schema_differences(database_url: str) -> list[Any]:
    """Return operations Alembic would generate for uncommitted model drift."""

    engine = create_engine(
        database_url,
        hide_parameters=True,
        poolclass=pool.NullPool,
    )
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(
                connection,
                opts={"compare_type": True},
            )
            return cast(list[Any], compare_metadata(context, Base.metadata))
    finally:
        engine.dispose()


def require_revisions(
    actual: tuple[str, ...],
    expected: tuple[str, ...],
    *,
    stage: str,
) -> None:
    if actual != expected:
        message = (
            f"unexpected database revision after {stage}: "
            f"expected {expected or ('<base>',)}, found {actual or ('<base>',)}"
        )
        raise MigrationValidationError(message)


def validate_migrations(
    database_url: str,
    *,
    output: Callable[[str], None] = print,
) -> None:
    """Validate the complete migration chain against an empty disposable database."""

    config = alembic_config(database_url)
    head = require_single_head(config)
    output(f"Alembic head: {head}")

    require_revisions(current_revisions(database_url), (), stage="initialization")

    command.upgrade(config, "head")
    require_revisions(current_revisions(database_url), (head,), stage="upgrade")
    output("Migration upgrade to head succeeded")

    command.downgrade(config, "base")
    require_revisions(current_revisions(database_url), (), stage="downgrade")
    output("Migration downgrade to base succeeded")

    command.upgrade(config, "head")
    require_revisions(current_revisions(database_url), (head,), stage="re-upgrade")
    output("Migration re-upgrade to head succeeded")

    differences = schema_differences(database_url)
    if differences:
        message = f"database schema differs from SQLAlchemy metadata ({len(differences)} changes)"
        raise MigrationValidationError(message)
    output("No uncommitted SQLAlchemy metadata changes detected")


def main() -> int:
    """Run validation without exposing connection details on failure."""

    try:
        settings = MigrationSettings()
        validate_migrations(settings.database.url.get_secret_value())
    except MigrationValidationError as error:
        sys.stderr.write(f"Migration validation failed: {error}\n")
        return 1
    except Exception as error:
        sys.stderr.write(f"Migration validation failed unexpectedly ({type(error).__name__})\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
