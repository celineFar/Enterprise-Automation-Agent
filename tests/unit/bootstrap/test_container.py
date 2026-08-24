from dataclasses import FrozenInstanceError
from unittest.mock import Mock

import pytest

from agent_platform.bootstrap.application import create_application_container
from agent_platform.config.settings import ApiSettings, WorkerSettings
from agent_platform.persistence.database import DatabaseRuntime


def api_settings() -> ApiSettings:
    return ApiSettings.model_validate(
        {
            "application": {
                "environment": "test",
                "deployment_id": "test-deployment",
            },
            "build": {
                "version": "test-version",
                "commit_sha": "test-commit",
                "image_digest": "test-image",
            },
            "database": {
                "url": "postgresql+psycopg://relay:secret@localhost:5432/relay",
            },
        }
    )


def worker_settings() -> WorkerSettings:
    return WorkerSettings.model_validate(
        {
            "application": {
                "environment": "test",
                "deployment_id": "test-deployment",
            },
            "build": {
                "version": "test-version",
                "commit_sha": "test-commit",
                "image_digest": "test-image",
            },
            "database": {
                "url": "postgresql+psycopg://relay:secret@localhost:5432/relay",
            },
        }
    )


@pytest.mark.parametrize("settings", [api_settings(), worker_settings()])
def test_composition_root_preserves_typed_process_dependencies(
    settings: ApiSettings | WorkerSettings,
) -> None:
    database = Mock(spec=DatabaseRuntime)

    container = create_application_container(settings, database)

    assert container.settings is settings
    assert container.database is database


def test_composition_root_creates_explicit_process_scoped_containers() -> None:
    settings = api_settings()
    database = Mock(spec=DatabaseRuntime)

    first = create_application_container(settings, database)
    second = create_application_container(settings, database)

    assert first is not second


def test_application_container_is_immutable() -> None:
    settings = api_settings()
    database = Mock(spec=DatabaseRuntime)
    container = create_application_container(settings, database)

    with pytest.raises(FrozenInstanceError):
        container.database = Mock(spec=DatabaseRuntime)  # type: ignore[misc]
