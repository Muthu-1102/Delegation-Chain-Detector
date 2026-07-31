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

from sqlalchemy import select
from app.models.tables import DelegationTokenRecord

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

async def save_token_chain(db: AsyncSession, token_chain: list[dict]) -> None:
    """Persist every token minted this run. This -- not a hand-written log
    line -- is the source of truth the audit trail is reconstructed from."""
    for payload in token_chain:
        existing = await db.execute(
            select(DelegationTokenRecord).where(DelegationTokenRecord.jwt_id == payload["jwt_id"])
        )
        if existing.scalar_one_or_none() is not None:
            continue

        db.add(
            DelegationTokenRecord(
                id=uuid.uuid4(),
                parent_token=payload["parent_jwt_id"],
                jwt_id=payload["jwt_id"],
                scope=",".join(payload["scope"]),
                issued_at=datetime.fromisoformat(payload["issued_at"]),
                expires_at=datetime.fromisoformat(payload["expires_at"]),
                task_id=uuid.UUID(payload["task_id"]),
                agent=payload["agent"],
                origin_user=payload["origin_user"],
                max_scope=",".join(payload["max_scope"]),
                depth=payload["depth"],
            )
        )
    await db.flush()


async def reconstruct_chain(db: AsyncSession, task_id: uuid.UUID) -> list[dict]:
    """Rebuild the full delegation chain for a task purely from persisted
    token payloads -- walking parent_token (jwt_id) links, not a separate
    log table."""
    result = await db.execute(
        select(DelegationTokenRecord)
        .where(DelegationTokenRecord.task_id == task_id)
        .order_by(DelegationTokenRecord.issued_at.asc())
    )
    rows = result.scalars().all()
    agent_by_jwt = {row.jwt_id: row.agent for row in rows}

    return [
        {
            "agent": row.agent,
            "parent_agent": agent_by_jwt.get(row.parent_token) if row.parent_token else None,
            "scope": row.scope.split(","),
            "max_scope": row.max_scope.split(","),
            "depth": row.depth,
            "origin_user": row.origin_user,
            "issued_at": row.issued_at.isoformat(),
            "expires_at": row.expires_at.isoformat(),
        }
        for row in rows
    ]
