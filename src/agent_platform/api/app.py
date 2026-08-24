from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI

from agent_platform.api.dependencies import get_container
from agent_platform.api.routes.health import router as health_router
from agent_platform.bootstrap.application import create_application_container
from agent_platform.bootstrap.container import ApplicationContainer
from agent_platform.bootstrap.lifecycle import database_lifespan
from agent_platform.config.settings import ApiSettings


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Own resources whose lifetime matches the API process."""

    settings: ApiSettings = application.state.settings
    async with database_lifespan(settings.database) as database:
        application.state.container = create_application_container(settings, database)
        try:
            yield
        finally:
            del application.state.container


def create_app(settings: ApiSettings | None = None) -> FastAPI:
    """Create the API application and validate its runtime configuration."""

    resolved_settings = settings or ApiSettings()
    application = FastAPI(
        title=resolved_settings.application.name,
        version=resolved_settings.build.version,
        lifespan=lifespan,
    )
    application.state.settings = resolved_settings

    api_router = APIRouter(prefix="/v1")

    @api_router.get("", include_in_schema=False)
    async def api_root(
        container: Annotated[ApplicationContainer[ApiSettings], Depends(get_container)],
    ) -> dict[str, str]:
        runtime_settings = container.settings
        return {
            "name": runtime_settings.application.name,
            "version": runtime_settings.build.version,
            "environment": runtime_settings.application.environment,
        }

    application.include_router(api_router)
    application.include_router(health_router)
    return application


app = create_app()
