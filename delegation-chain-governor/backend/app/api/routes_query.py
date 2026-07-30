from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import pending_approvals, workflow_store
from app.core.audit import log_delegation, log_execution
from app.core.graph import run_workflow
from app.db.session import async_session_factory, get_db
from app.schemas import QueryRequest, QueryResponse

router = APIRouter(prefix="/api/query", tags=["query"])

_CHAIN = [
    ("gateway_agent", "planner_agent", ["finance:read", "finance:report", "report:generate"]),
    ("planner_agent", "finance_agent", ["finance:read", "finance:report"]),
    ("finance_agent", "report_agent", ["report:generate"]),
]


async def _persist_chain(request_id: str, up_to_index: int, final_status: str) -> None:
    async with async_session_factory() as db:
        for i, (parent, child, scope) in enumerate(_CHAIN):
            if i > up_to_index:
                break
            status = "approved" if i < up_to_index else final_status
            await log_delegation(
                db,
                request_id=uuid.UUID(request_id),
                parent_agent=parent,
                child_agent=child,
                delegated_scope=scope,
                status=status,
            )
        await log_execution(
            db,
            request_id=uuid.UUID(request_id),
            agent="report_agent" if final_status == "approved" else "finance_agent",
            execution_time=0.0,
            status="success" if final_status == "approved" else "failure",
            message=final_status,
        )
        await db.commit()


async def _execute_and_persist(request_id: str, query: str) -> None:
    final_state = await run_workflow(request_id=request_id, query=query)
    status = final_state.get("status", "failed")

    if status == "pending_approval":
        # Halt gracefully. Save resumable state, log the rejected hop, and
        # surface a clear structured warning to the UI -- no exception.
        pending_approvals.save(request_id, final_state)
        workflow_store.update(
            request_id,
            status="pending_approval",
            current_agent="finance_agent",
            plan=final_state.get("plan"),
            finance_result=final_state.get("finance_result"),
            escalation=final_state.get("escalation"),
            error=None,
        )
        await _persist_chain(request_id, up_to_index=2, final_status="rejected_scope")
        return

    workflow_store.update(
        request_id,
        status=status,
        current_agent="report_agent" if status == "completed" else "unknown",
        plan=final_state.get("plan"),
        finance_result=final_state.get("finance_result"),
        report_result=final_state.get("report_result"),
        error=final_state.get("error"),
    )
    await _persist_chain(
        request_id,
        up_to_index=3,
        final_status="approved" if status == "completed" else "rejected_scope",
    )


@router.post("", response_model=QueryResponse)
async def submit_query(
    payload: QueryRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> QueryResponse:
    request_id = str(uuid.uuid4())
    workflow_store.create(request_id, payload.query)
    background_tasks.add_task(_execute_and_persist, request_id, payload.query)
    return QueryResponse(request_id=request_id, status="running")