from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.agents import report
from app.agents.state import DelegationState
from app.core import pending_approvals, workflow_store
from app.core.audit import log_delegation, log_execution
from app.core.governor import governor
from app.db.session import async_session_factory
from app.schemas import ResolveDecisionRequest, WorkflowStatusResponse

from app.core.audit import log_delegation, log_execution, save_token_chain
from app.core.governor import ScopeEscalationError, governor

router = APIRouter(prefix="/api/workflow", tags=["workflow"])




async def _grant_and_resume(request_id: str, state: DelegationState) -> None:
    parent_token = governor.verify(state["token"])
    escalation = state["escalation"]

    try:
        override_token = governor.issue_override_token(
            parent_token=parent_token,
            child_agent="report_agent",
            requested_scope=escalation["requested_scope"],
        )
    except ScopeEscalationError as exc:
        # Even a human override can never exceed the task's max_scope ceiling.
        workflow_store.update(request_id, status="failed", error=f"Override denied: {exc}", escalation=None)
        return

    resumed_state = {
        **state,
        "token": override_token.encoded,
        "scope": override_token.scope,
        "token_chain": [*state.get("token_chain", []), governor.to_public_dict(override_token)],
    }
    final_state = await report.run(resumed_state)

    workflow_store.update(
        request_id,
        status=final_state.get("status", "failed"),
        current_agent="report_agent",
        report_result=final_state.get("report_result"),
        escalation=None,
        note="Elevated access was granted by user override (still within the task's original max scope).",
    )

    async with async_session_factory() as db:
        await save_token_chain(db, final_state.get("token_chain", []))
        await log_delegation(
            db,
            request_id=uuid.UUID(request_id),
            parent_agent=escalation["parent_agent"],
            child_agent=escalation["child_agent"],
            delegated_scope=escalation["requested_scope"],
            status="approved_override",
        )
        await log_execution(
            db, request_id=uuid.UUID(request_id), agent="report_agent",
            execution_time=0.0, status="success",
            message="Completed after user-approved scope override.",
        )
        await db.commit()


async def _deny(request_id: str, state: DelegationState) -> None:
    escalation = state["escalation"]

    workflow_store.update(
        request_id,
        status="completed",
        current_agent="finance_agent",
        report_result=None,
        escalation=None,
        note="Report generation was skipped: elevated access was denied.",
    )

    async with async_session_factory() as db:
        await log_delegation(
            db,
            request_id=uuid.UUID(request_id),
            parent_agent=escalation["parent_agent"],
            child_agent=escalation["child_agent"],
            delegated_scope=escalation["requested_scope"],
            status="rejected_scope_denied_by_user",
        )
        await log_execution(
            db,
            request_id=uuid.UUID(request_id),
            agent="finance_agent",
            execution_time=0.0,
            status="success",
            message="Workflow completed with finance results only; report step denied by user.",
        )
        await db.commit()


@router.post("/{request_id}/resolve", response_model=WorkflowStatusResponse)
async def resolve_escalation(
    request_id: str,
    payload: ResolveDecisionRequest,
    background_tasks: BackgroundTasks,
) -> WorkflowStatusResponse:
    state = pending_approvals.pop(request_id)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending approval found for this request_id",
        )

    workflow_store.update(request_id, status="resolving")

    if payload.decision == "grant":
        background_tasks.add_task(_grant_and_resume, request_id, state)
    else:
        background_tasks.add_task(_deny, request_id, state)

    return WorkflowStatusResponse(**workflow_store.get(request_id))