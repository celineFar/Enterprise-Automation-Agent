import importlib

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

import agent_platform.bootstrap.lifecycle as lifecycle_module
from agent_platform.config.settings import ApiSettings
from agent_platform.persistence.database import create_database_runtime


@pytest.mark.integration
def test_api_starts_reports_ready_and_disposes_engine(
    api_settings: ApiSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = create_database_runtime(api_settings.database)
    closed_connections = 0

    def record_close(_connection: object, _record: object) -> None:
        nonlocal closed_connections
        closed_connections += 1

    event.listen(runtime.engine.sync_engine, "close", record_close)
    monkeypatch.setattr(lifecycle_module, "create_database_runtime", lambda _settings: runtime)

    app_module = importlib.import_module("agent_platform.api.app")
    application = app_module.create_app(api_settings)

    with TestClient(application) as client:
        assert hasattr(application.state, "database")
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    assert not hasattr(application.state, "database")
    assert closed_connections >= 1
