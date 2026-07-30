"""
Immutable audit trail helpers.

Writes to `delegation_logs` (every handoff the Governor approves or rejects)
and `execution_logs` (every agent execution result). These tables are
append-only by convention -- no update/delete paths are exposed anywhere in
the API layer.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tables import DelegationLog, ExecutionLog

DelegationStatus = Literal["approved", "rejected_scope", "rejected_expired", "rejected_invalid"]
ExecutionStatus = Literal["success", "failure", "running"]


async def log_delegation(
    db: AsyncSession,
    request_id: uuid.UUID,
    parent_agent: str,
    child_agent: str,
    delegated_scope: list[str],
    status: DelegationStatus,
) -> None:
    entry = DelegationLog(
        id=uuid.uuid4(),
        request_id=request_id,
        parent_agent=parent_agent,
        child_agent=child_agent,
        delegated_scope=",".join(delegated_scope),
        status=status,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(entry)
    await db.flush()


async def log_execution(
    db: AsyncSession,
    request_id: uuid.UUID,
    agent: str,
    execution_time: float,
    status: ExecutionStatus,
    message: str = "",
) -> None:
    entry = ExecutionLog(
        id=uuid.uuid4(),
        request_id=request_id,
        agent=agent,
        execution_time=execution_time,
        status=status,
        message=message,
    )
    db.add(entry)
    await db.flush()
