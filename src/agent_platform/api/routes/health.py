from typing import Annotated, Literal

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from agent_platform.api.dependencies import get_database
from agent_platform.persistence.database import DatabaseRuntime

router = APIRouter(include_in_schema=False)


@router.get("/health")
async def health() -> dict[str, Literal["healthy"]]:
    """Report process liveness without checking external dependencies."""

    return {"status": "healthy"}


@router.get("/ready")
async def readiness(
    database: Annotated[DatabaseRuntime, Depends(get_database)],
) -> JSONResponse:
    """Report whether the API's required PostgreSQL dependency is available."""

    try:
        await database.check_connection()
    except SQLAlchemyError:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready"},
        )

    return JSONResponse(content={"status": "ready"})
