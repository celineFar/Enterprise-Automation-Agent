import importlib
import sys
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from agent_platform.bootstrap.container import ApplicationContainer
from agent_platform.config.settings import ApiSettings
from agent_platform.persistence.database import DatabaseRuntime

APP_MODULE = "agent_platform.api.app"


@pytest.fixture
def api_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    values = {
        "AGENT_APPLICATION__NAME": "relay-test-api",
        "AGENT_APPLICATION__ENVIRONMENT": "test",
        "AGENT_APPLICATION__DEPLOYMENT_ID": "api-unit-tests",
        "AGENT_BUILD__VERSION": "0.1.0-test",
        "AGENT_BUILD__COMMIT_SHA": "abc123",
        "AGENT_BUILD__IMAGE_DIGEST": "sha256:test",
        "AGENT_DATABASE__URL": "postgresql+psycopg://relay:secret@localhost:5432/relay",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)

    sys.modules.pop(APP_MODULE, None)
    yield
    sys.modules.pop(APP_MODULE, None)


def test_factory_creates_configured_fastapi_application(api_environment: None) -> None:
    app_module = importlib.import_module(APP_MODULE)
    settings = ApiSettings()

    application = app_module.create_app(settings)

    assert isinstance(application, FastAPI)
    assert application.title == "relay-test-api"
    assert application.version == "0.1.0-test"
    assert application.state.settings is settings


def test_v1_api_root_exposes_non_secret_runtime_identity(
    api_environment: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app_module = importlib.import_module(APP_MODULE)
    database = Mock(spec=DatabaseRuntime)
    container_present_during_database_cleanup: bool | None = None

    @asynccontextmanager
    async def fake_database_lifespan(_settings: object) -> AsyncIterator[DatabaseRuntime]:
        nonlocal container_present_during_database_cleanup
        try:
            yield database
        finally:
            container_present_during_database_cleanup = hasattr(
                application.state,
                "container",
            )

    monkeypatch.setattr(app_module, "database_lifespan", fake_database_lifespan)
    application = app_module.create_app(ApiSettings())

    with TestClient(application) as client:
        container = application.state.container
        assert isinstance(container, ApplicationContainer)
        assert container.settings is application.state.settings
        assert container.database is database
        assert not hasattr(application.state, "database")
        response = client.get("/v1")

    assert not hasattr(application.state, "container")
    assert container_present_during_database_cleanup is False
    assert response.status_code == 200
    assert response.json() == {
        "name": "relay-test-api",
        "version": "0.1.0-test",
        "environment": "test",
    }
    assert "secret" not in response.text


def test_factory_fails_when_required_configuration_is_missing(
    api_environment: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app_module = importlib.import_module(APP_MODULE)
    monkeypatch.delenv("AGENT_DATABASE__URL")

    with pytest.raises(ValidationError):
        app_module.create_app()


def test_module_exposes_application_entry_point(api_environment: None) -> None:
    app_module = importlib.import_module(APP_MODULE)

    assert isinstance(app_module.app, FastAPI)
