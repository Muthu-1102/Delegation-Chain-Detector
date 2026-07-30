from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.tables import ExecutionLog
from app.schemas import ExecutionLogEntry

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("", response_model=list[ExecutionLogEntry])
async def get_execution_logs(db: AsyncSession = Depends(get_db)) -> list[ExecutionLogEntry]:
    result = await db.execute(select(ExecutionLog).order_by(ExecutionLog.id.desc()).limit(200))
    rows = result.scalars().all()

    return [
        ExecutionLogEntry(
            request_id=str(row.request_id),
            agent=row.agent,
            execution_time=row.execution_time,
            status=row.status,
            message=row.message or "",
        )
        for row in rows
    ]
