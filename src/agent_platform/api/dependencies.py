from typing import Annotated

from fastapi import Depends, Request

from agent_platform.bootstrap.container import ApplicationContainer
from agent_platform.config.settings import ApiSettings
from agent_platform.persistence.database import DatabaseRuntime


def get_container(request: Request) -> ApplicationContainer[ApiSettings]:
    """Resolve the API process container at the HTTP boundary."""

    container: ApplicationContainer[ApiSettings] = request.app.state.container
    return container


def get_database(
    container: Annotated[ApplicationContainer[ApiSettings], Depends(get_container)],
) -> DatabaseRuntime:
    """Resolve the process-owned database runtime from the API container."""

    return container.database
