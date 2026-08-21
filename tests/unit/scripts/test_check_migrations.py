from unittest.mock import Mock, call

import pytest
from alembic.config import Config
from scripts import check_migrations


def test_require_single_head_rejects_divergent_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scripts = Mock()
    scripts.get_heads.return_value = ["head_one", "head_two"]
    monkeypatch.setattr(
        "scripts.check_migrations.ScriptDirectory.from_config",
        lambda _config: scripts,
    )

    with pytest.raises(
        check_migrations.MigrationValidationError,
        match="expected exactly one Alembic head, found 2",
    ):
        check_migrations.require_single_head(Config())


def test_validate_migrations_checks_round_trip_and_schema_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = Config()
    outputs: list[str] = []
    revisions = iter(
        (
            (),
            ("migration_head",),
            (),
            ("migration_head",),
        )
    )
    upgrade = Mock()
    downgrade = Mock()

    monkeypatch.setattr(check_migrations, "alembic_config", lambda _url: config)
    monkeypatch.setattr(check_migrations, "require_single_head", lambda _config: "migration_head")
    monkeypatch.setattr(check_migrations, "current_revisions", lambda _url: next(revisions))
    monkeypatch.setattr(check_migrations, "schema_differences", lambda _url: [])
    monkeypatch.setattr("scripts.check_migrations.command.upgrade", upgrade)
    monkeypatch.setattr("scripts.check_migrations.command.downgrade", downgrade)

    check_migrations.validate_migrations(
        "postgresql+psycopg://relay:secret@localhost/relay",
        output=outputs.append,
    )

    assert upgrade.call_args_list == [call(config, "head"), call(config, "head")]
    downgrade.assert_called_once_with(config, "base")
    assert outputs == [
        "Alembic head: migration_head",
        "Migration upgrade to head succeeded",
        "Migration downgrade to base succeeded",
        "Migration re-upgrade to head succeeded",
        "No uncommitted SQLAlchemy metadata changes detected",
    ]


def test_validate_migrations_rejects_schema_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    revisions = iter(((), ("migration_head",), (), ("migration_head",)))
    monkeypatch.setattr(check_migrations, "alembic_config", lambda _url: Config())
    monkeypatch.setattr(check_migrations, "require_single_head", lambda _config: "migration_head")
    monkeypatch.setattr(check_migrations, "current_revisions", lambda _url: next(revisions))
    monkeypatch.setattr(check_migrations, "schema_differences", lambda _url: [("add_table",)])
    monkeypatch.setattr(
        "scripts.check_migrations.command.upgrade",
        lambda _config, _revision: None,
    )
    monkeypatch.setattr(
        "scripts.check_migrations.command.downgrade",
        lambda _config, _revision: None,
    )

    with pytest.raises(
        check_migrations.MigrationValidationError,
        match=r"SQLAlchemy metadata \(1 changes\)",
    ):
        check_migrations.validate_migrations(
            "postgresql+psycopg://relay:secret@localhost/relay",
            output=lambda _message: None,
        )


def test_main_redacts_unexpected_dependency_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    database_url = "postgresql+psycopg://relay:secret@localhost/relay"
    settings = Mock()
    settings.database.url.get_secret_value.return_value = database_url
    monkeypatch.setattr(check_migrations, "MigrationSettings", lambda: settings)
    monkeypatch.setattr(
        check_migrations,
        "validate_migrations",
        Mock(side_effect=RuntimeError(database_url)),
    )

    assert check_migrations.main() == 1
    output = capsys.readouterr().err
    assert "secret" not in output
    assert database_url not in output
    assert "RuntimeError" in output
