import pytest
from pydantic import ValidationError

from agent_platform.config.settings import ApiSettings, MigrationSettings, WorkerSettings


@pytest.fixture
def shared_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    values = {
        "AGENT_APPLICATION__ENVIRONMENT": "test",
        "AGENT_APPLICATION__DEPLOYMENT_ID": "unit-tests",
        "AGENT_BUILD__VERSION": "0.1.0-test",
        "AGENT_BUILD__COMMIT_SHA": "abc123",
        "AGENT_BUILD__IMAGE_DIGEST": "sha256:test",
        "AGENT_DATABASE__URL": "postgresql+psycopg://relay:secret@localhost:5432/relay",
    }

    for name, value in values.items():
        monkeypatch.setenv(name, value)


def test_api_settings_load_nested_environment(
    shared_environment: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AGENT_API__PORT", "9000")

    settings = ApiSettings()

    assert settings.application.environment == "test"
    assert settings.api.port == 9000
    assert settings.database.pool_size == 5


def test_worker_does_not_require_api_settings(shared_environment: None) -> None:
    settings = WorkerSettings()

    assert settings.worker.poll_interval_seconds == 1
    assert not hasattr(settings, "api")


def test_migration_requires_only_database_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "AGENT_DATABASE__URL",
        "postgresql+psycopg://relay:secret@localhost:5432/relay",
    )

    settings = MigrationSettings()

    assert settings.database.url.get_secret_value().startswith("postgresql+psycopg://")


def test_missing_database_url_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AGENT_DATABASE__URL", raising=False)

    with pytest.raises(ValidationError):
        MigrationSettings()


@pytest.mark.parametrize(
    "url",
    [
        "not-a-url",
        "sqlite:///relay.db",
        "postgresql+psycopg://relay:secret@localhost:5432",
    ],
)
def test_invalid_database_url_fails(
    monkeypatch: pytest.MonkeyPatch,
    url: str,
) -> None:
    monkeypatch.setenv("AGENT_DATABASE__URL", url)

    with pytest.raises(ValidationError):
        MigrationSettings()


def test_invalid_api_port_fails(
    shared_environment: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AGENT_API__PORT", "70000")

    with pytest.raises(ValidationError):
        ApiSettings()


def test_enabled_telemetry_requires_endpoint(
    shared_environment: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AGENT_TELEMETRY__ENABLED", "true")
    monkeypatch.delenv("AGENT_TELEMETRY__OTLP_ENDPOINT", raising=False)

    with pytest.raises(ValidationError):
        ApiSettings()


def test_database_secret_is_not_exposed(shared_environment: None) -> None:
    settings = ApiSettings()

    assert "secret" not in repr(settings)

