"""
Workflow status store, persisted in Postgres (`workflow_records`).

This used to be an in-memory dict guarded by a threading.Lock. That meant:
  - a container restart silently lost every workflow's status
  - running more than one backend replica gave each replica its own,
    inconsistent view of workflow state
  - a request that landed on replica A but polled against replica B would
    get 404s

All functions now take an AsyncSession and only `flush()` -- the caller
owns the transaction boundary (commit/rollback), consistent with
app.core.audit's convention.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tables import WorkflowRecord


async def create(db: AsyncSession, request_id: str, query: str) -> None:
    now = datetime.now(timezone.utc)
    db.add(
        WorkflowRecord(
            request_id=uuid.UUID(request_id),
            query=query,
            status="running",
            current_agent="gateway_agent",
            plan=None,
            finance_result=None,
            report_result=None,
            error=None,
            escalation=None,
            note=None,
            created_at=now,
            updated_at=now,
        )
    )
    await db.flush()


async def update(db: AsyncSession, request_id: str, **fields: Any) -> None:
    result = await db.execute(
        select(WorkflowRecord).where(WorkflowRecord.request_id == uuid.UUID(request_id))
    )
    record = result.scalar_one_or_none()
    if record is None:
        return
    for key, value in fields.items():
        setattr(record, key, value)
    record.updated_at = datetime.now(timezone.utc)
    await db.flush()


async def get(db: AsyncSession, request_id: str) -> dict[str, Any] | None:
    result = await db.execute(
        select(WorkflowRecord).where(WorkflowRecord.request_id == uuid.UUID(request_id))
    )
    record = result.scalar_one_or_none()
    if record is None:
        return None
    return {
        "request_id": str(record.request_id),
        "query": record.query,
        "status": record.status,
        "current_agent": record.current_agent,
        "plan": record.plan,
        "finance_result": record.finance_result,
        "report_result": record.report_result,
        "error": record.error,
        "escalation": record.escalation,
        "note": record.note,
    }