from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import pending_approvals, workflow_store
from app.core.audit import log_delegation, log_execution, save_token_chain
from app.core.graph import run_workflow
from app.db.session import async_session_factory, get_db
from app.schemas import QueryRequest, QueryResponse

router = APIRouter(prefix="/api/query", tags=["query"])
logger = logging.getLogger("dcg")

_CHAIN = [
    ("gateway_agent", "planner_agent", ["finance:read", "finance:report", "report:generate"]),
    ("planner_agent", "finance_agent", ["finance:read", "finance:report"]),
    ("finance_agent", "report_agent", ["report:generate"]),
]


async def _persist_chain(db: AsyncSession, request_id: str, up_to_index: int, final_status: str) -> None:
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


async def _execute_and_persist(request_id: str, query: str, origin_user: str) -> None:
    """
    Background task -- runs after the client already has its 200 OK.
    Exceptions here do NOT surface to the HTTP response; Starlette just
    logs them and drops the task. Without an explicit safety net, any
    failure below (graph execution, DB write, transient network issue)
    leaves the workflow_records row exactly as `create()` left it
    (status="running") forever, and the frontend polls indefinitely
    since it only stops on a terminal status. The try/except below
    guarantees a terminal write no matter what goes wrong.
    """
    try:
        final_state = await run_workflow(request_id=request_id, query=query, origin_user=origin_user)
        status = final_state.get("status", "failed")

        async with async_session_factory() as db:
            await save_token_chain(db, final_state.get("token_chain", []))

            if status == "pending_approval":
                await pending_approvals.save(db, request_id, final_state)
                await workflow_store.update(
                    db,
                    request_id,
                    status="pending_approval",
                    current_agent="finance_agent",
                    plan=final_state.get("plan"),
                    finance_result=final_state.get("finance_result"),
                    escalation=final_state.get("escalation"),
                    error=None,
                )
                await _persist_chain(db, request_id, up_to_index=2, final_status="rejected_scope")
                await db.commit()
                return

            await workflow_store.update(
                db,
                request_id,
                status=status,
                current_agent="report_agent" if status == "completed" else "unknown",
                plan=final_state.get("plan"),
                finance_result=final_state.get("finance_result"),
                report_result=final_state.get("report_result"),
                error=final_state.get("error"),
            )
            await _persist_chain(
                db, request_id, up_to_index=3, final_status="approved" if status == "completed" else "rejected_scope"
            )
            await db.commit()

    except Exception as exc:  # noqa: BLE001 -- deliberately broad: this is the last-resort safety net
        logger.exception("Workflow %s failed in background execution", request_id)
        try:
            async with async_session_factory() as db:
                await workflow_store.update(
                    db,
                    request_id,
                    status="failed",
                    current_agent="unknown",
                    error=f"Internal error during workflow execution: {exc}",
                )
                await db.commit()
        except Exception:
            # If even the failure-write fails (e.g. DB is genuinely down),
            # there's nothing more we can do from here -- this is now
            # something your alerting/observability needs to catch (Phase 6),
            # not something the request/response cycle can fix.
            logger.exception("Also failed to write terminal 'failed' status for workflow %s", request_id)


@router.post("", response_model=QueryResponse)
async def submit_query(
    payload: QueryRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
) -> QueryResponse:
    request_id = str(uuid.uuid4())
    await workflow_store.create(db, request_id, payload.query)
    await db.commit()
    background_tasks.add_task(_execute_and_persist, request_id, payload.query, payload.user)
    return QueryResponse(request_id=request_id, status="running")