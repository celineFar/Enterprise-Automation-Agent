from typing import Annotated
from unittest.mock import Mock

from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from agent_platform.api.dependencies import get_container, get_database
from agent_platform.bootstrap.application import create_application_container
from agent_platform.bootstrap.container import ApplicationContainer
from agent_platform.config.settings import ApiSettings
from agent_platform.persistence.database import DatabaseRuntime


def api_settings() -> ApiSettings:
    return ApiSettings.model_validate(
        {
            "application": {
                "environment": "test",
                "deployment_id": "dependency-tests",
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


def test_get_container_resolves_process_container_from_request_state() -> None:
    container = create_application_container(
        api_settings(),
        Mock(spec=DatabaseRuntime),
    )
    request = Mock(spec=Request)
    request.app.state.container = container

    assert get_container(request) is container


def test_get_database_resolves_database_from_container() -> None:
    database = Mock(spec=DatabaseRuntime)
    container = create_application_container(api_settings(), database)

    assert get_database(container) is database


def test_fastapi_boundary_dependency_can_be_overridden() -> None:
    database = Mock(spec=DatabaseRuntime)
    container = create_application_container(api_settings(), database)
    application = FastAPI()

    @application.get("/")
    async def dependency_identity(
        resolved: Annotated[ApplicationContainer[ApiSettings], Depends(get_container)],
    ) -> dict[str, bool]:
        return {"matches": resolved is container}

    application.dependency_overrides[get_container] = lambda: container

    with TestClient(application) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"matches": True}
