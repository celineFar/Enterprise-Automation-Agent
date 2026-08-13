import importlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from agent_platform.config.settings import ApiSettings
from agent_platform.persistence.database import DatabaseRuntime

APP_MODULE = "agent_platform.api.app"


@pytest.fixture
def settings(monkeypatch: pytest.MonkeyPatch) -> ApiSettings:
    values = {
        "AGENT_APPLICATION__ENVIRONMENT": "test",
        "AGENT_APPLICATION__DEPLOYMENT_ID": "health-tests",
        "AGENT_BUILD__VERSION": "0.1.0-test",
        "AGENT_BUILD__COMMIT_SHA": "abc123",
        "AGENT_BUILD__IMAGE_DIGEST": "sha256:test",
        "AGENT_DATABASE__URL": "postgresql+psycopg://relay:secret@localhost:5432/relay",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)
    return ApiSettings()


@pytest.fixture
def database() -> Mock:
    runtime = Mock(spec=DatabaseRuntime)
    runtime.check_connection = AsyncMock()
    return runtime


@pytest.fixture
def client(
    settings: ApiSettings,
    database: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    app_module = importlib.import_module(APP_MODULE)

    @asynccontextmanager
    async def fake_database_lifespan(_settings: object) -> AsyncIterator[DatabaseRuntime]:
        yield database

    monkeypatch.setattr(app_module, "database_lifespan", fake_database_lifespan)
    return TestClient(app_module.create_app(settings))


def test_health_reports_liveness_without_querying_database(
    client: TestClient,
    database: Mock,
) -> None:
    with client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
    database.check_connection.assert_not_awaited()


def test_readiness_succeeds_when_postgres_responds(
    client: TestClient,
    database: Mock,
) -> None:
    with client:
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    database.check_connection.assert_awaited_once_with()


def test_database_outage_fails_readiness_but_not_liveness(
    client: TestClient,
    database: Mock,
) -> None:
    database.check_connection.side_effect = OperationalError(
        "postgresql+psycopg://relay:secret@localhost/relay",
        {},
        ConnectionError("database unavailable: secret"),
    )

    with client:
        readiness_response = client.get("/ready")
        health_response = client.get("/health")

    assert readiness_response.status_code == 503
    assert readiness_response.json() == {"status": "not_ready"}
    assert "secret" not in readiness_response.text
    assert health_response.status_code == 200
    assert health_response.json() == {"status": "healthy"}


def test_readiness_does_not_hide_unexpected_programming_errors(
    client: TestClient,
    database: Mock,
) -> None:
    database.check_connection.side_effect = RuntimeError("programming error")

    with client, pytest.raises(RuntimeError, match="programming error"):
        client.get("/ready")
