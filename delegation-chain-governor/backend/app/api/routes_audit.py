from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.tables import DelegationLog
from app.schemas import AuditResponse, DelegationLogEntry

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/{request_id}", response_model=AuditResponse)
async def get_audit_trail(request_id: str, db: AsyncSession = Depends(get_db)) -> AuditResponse:
    result = await db.execute(
        select(DelegationLog)
        .where(DelegationLog.request_id == uuid.UUID(request_id))
        .order_by(DelegationLog.timestamp.asc())
    )
    rows = result.scalars().all()

    chain = [
        DelegationLogEntry(
            parent_agent=row.parent_agent,
            child_agent=row.child_agent,
            delegated_scope=row.delegated_scope,
            status=row.status,
            timestamp=row.timestamp.isoformat(),
        )
        for row in rows
    ]

    return AuditResponse(request_id=request_id, chain=chain)
