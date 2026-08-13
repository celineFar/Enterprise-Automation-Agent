from typing import Literal

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from agent_platform.persistence.database import DatabaseRuntime

router = APIRouter(include_in_schema=False)


@router.get("/health")
async def health() -> dict[str, Literal["healthy"]]:
    """Report process liveness without checking external dependencies."""

    return {"status": "healthy"}


@router.get("/ready")
async def readiness(
    request: Request,
) -> JSONResponse:
    """Report whether the API's required PostgreSQL dependency is available."""

    database: DatabaseRuntime = request.app.state.database
    try:
        await database.check_connection()
    except SQLAlchemyError:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready"},
        )

    return JSONResponse(content={"status": "ready"})
