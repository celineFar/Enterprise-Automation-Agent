from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request

from agent_platform.config.settings import ApiSettings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Own resources whose lifetime matches the API process."""

    yield


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
    async def api_root(request: Request) -> dict[str, str]:
        runtime_settings: ApiSettings = request.app.state.settings
        return {
            "name": runtime_settings.application.name,
            "version": runtime_settings.build.version,
            "environment": runtime_settings.application.environment,
        }

    application.include_router(api_router)
    return application


app = create_app()
