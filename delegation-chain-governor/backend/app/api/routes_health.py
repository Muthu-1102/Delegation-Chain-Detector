from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness probe -- process is up. Does not touch the DB, so a slow/
    down database doesn't cause the container orchestrator to kill and
    restart a healthy process."""
    return HealthResponse()


@router.get("/health/ready")
async def readiness(response: Response, db: AsyncSession = Depends(get_db)) -> dict:
    """Readiness probe -- use this one for load-balancer / orchestrator
    routing decisions. Fails (503) if the database is unreachable."""
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready", "database": "unreachable"}
    return {"status": "ready", "database": "ok"}