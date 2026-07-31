from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import reconstruct_chain
from app.db.session import get_db
from app.models.tables import DelegationLog
from app.schemas import AuditResponse, DelegationLogEntry, TokenChainEntry

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/{request_id}", response_model=AuditResponse)
async def get_audit_trail(request_id: str, db: AsyncSession = Depends(get_db)) -> AuditResponse:
    task_id = uuid.UUID(request_id)

    chain_rows = await reconstruct_chain(db, task_id)
    chain = [TokenChainEntry(**row) for row in chain_rows]

    result = await db.execute(
        select(DelegationLog).where(DelegationLog.request_id == task_id).order_by(DelegationLog.timestamp.asc())
    )
    decisions = [
        DelegationLogEntry(
            parent_agent=row.parent_agent,
            child_agent=row.child_agent,
            delegated_scope=row.delegated_scope,
            status=row.status,
            timestamp=row.timestamp.isoformat(),
        )
        for row in result.scalars().all()
    ]

    return AuditResponse(request_id=request_id, chain=chain, decisions=decisions)