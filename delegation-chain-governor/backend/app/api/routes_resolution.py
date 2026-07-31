from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import report
from app.agents.state import DelegationState
from app.core import pending_approvals, workflow_store
from app.core.audit import log_delegation, log_execution, save_token_chain
from app.core.governor import ScopeEscalationError, governor
from app.db.session import async_session_factory, get_db
from app.schemas import ResolveDecisionRequest, WorkflowStatusResponse

router = APIRouter(prefix="/api/workflow", tags=["workflow"])


async def _grant_and_resume(request_id: str, state: DelegationState) -> None:
    parent_token = governor.verify(state["token"])
    escalation = state["escalation"]

    async with async_session_factory() as db:
        try:
            override_token = governor.issue_override_token(
                parent_token=parent_token,
                child_agent="report_agent",
                requested_scope=escalation["requested_scope"],
            )
        except ScopeEscalationError as exc:
            # Even a human override can never exceed the task's max_scope ceiling.
            await workflow_store.update(
                db, request_id, status="failed", error=f"Override denied: {exc}", escalation=None
            )
            await db.commit()
            return

        resumed_state = {
            **state,
            "token": override_token.encoded,
            "scope": override_token.scope,
            "token_chain": [*state.get("token_chain", []), governor.to_public_dict(override_token)],
        }
        final_state = await report.run(resumed_state)

        await workflow_store.update(
            db,
            request_id,
            status=final_state.get("status", "failed"),
            current_agent="report_agent",
            report_result=final_state.get("report_result"),
            escalation=None,
            note="Elevated access was granted by user override (still within the task's original max scope).",
        )

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

    async with async_session_factory() as db:
        await workflow_store.update(
            db,
            request_id,
            status="completed",
            current_agent="finance_agent",
            report_result=None,
            escalation=None,
            note="Report generation was skipped: elevated access was denied.",
        )

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
    db: AsyncSession = Depends(get_db),
) -> WorkflowStatusResponse:
    state = await pending_approvals.pop(db, request_id)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending approval found for this request_id",
        )

    await workflow_store.update(db, request_id, status="resolving")
    await db.commit()

    if payload.decision == "grant":
        background_tasks.add_task(_grant_and_resume, request_id, state)
    else:
        background_tasks.add_task(_deny, request_id, state)

    workflow = await workflow_store.get(db, request_id)
    return WorkflowStatusResponse(**workflow)