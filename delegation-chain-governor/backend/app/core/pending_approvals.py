"""
Store for workflows paused on a scope-escalation decision, persisted in
Postgres (`pending_approvals`).

When the Governor blocks a delegation, the workflow halts instead of
crashing. The full DelegationState needed to resume it (or gracefully
finish without the blocked step) is kept here until the user calls
POST /api/workflow/{request_id}/resolve.

Previously in-memory: a restart, deploy, or second replica meant a pending
approval could vanish, permanently stranding that workflow in
"pending_approval" with no way to ever resolve it -- a real correctness
bug for a system whose whole selling point is a reliable audit trail.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tables import PendingApprovalRecord


async def save(db: AsyncSession, request_id: str, state: dict[str, Any]) -> None:
    db.add(
        PendingApprovalRecord(
            request_id=uuid.UUID(request_id),
            state=state,
            created_at=datetime.now(timezone.utc),
        )
    )
    await db.flush()


async def pop(db: AsyncSession, request_id: str) -> dict[str, Any] | None:
    result = await db.execute(
        select(PendingApprovalRecord).where(PendingApprovalRecord.request_id == uuid.UUID(request_id))
    )
    record = result.scalar_one_or_none()
    if record is None:
        return None
    state = record.state
    await db.delete(record)
    await db.flush()
    return state


async def peek(db: AsyncSession, request_id: str) -> dict[str, Any] | None:
    result = await db.execute(
        select(PendingApprovalRecord).where(PendingApprovalRecord.request_id == uuid.UUID(request_id))
    )
    record = result.scalar_one_or_none()
    return record.state if record else None