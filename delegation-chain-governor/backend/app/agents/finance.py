"""
Finance Agent.

Consumes the token delegated by the Planner Agent. Requires 'finance:read'
scope; will refuse to run without it. Produces a finance result and then
attempts to delegate onward to the Report Agent. If that delegation would
exceed the scope Finance itself holds, the workflow does NOT crash --
it pauses in a "pending_approval" state so a human can decide whether to
grant an explicit override or deny the request.
"""

from __future__ import annotations

from app.agents.llm import complete
from app.agents.state import DelegationState
from app.core.governor import ScopeEscalationError, governor

AGENT_NAME = "finance_agent"
REQUIRED_SCOPE = "finance:read"

SYSTEM_PROMPT = (
    "You are the Finance Agent. Given a plan, produce a concise financial "
    "analysis or figures relevant to the request. Do not fabricate exact "
    "real-world data; clearly mark illustrative figures as such."
)


async def run(state: DelegationState) -> DelegationState:
    token = governor.verify(state["token"])

    if REQUIRED_SCOPE not in token.scope:
        return {
            **state,
            "status": "failed",
            "error": f"finance_agent missing required scope '{REQUIRED_SCOPE}'",
        }

    result = await complete(SYSTEM_PROMPT, state["plan"])
    requested_scope = ["report:generate"]

    try:
        delegated_token = governor.delegate(
            parent_token=token,
            child_agent="report_agent",
            requested_scope=requested_scope,
        )
    except ScopeEscalationError as exc:
        # Blocked delegation -> pause, don't crash. The Governor caught a
        # real scope-escalation attempt; surface it as a decision for a
        # human instead of an unhandled exception.
        return {
            **state,
            "finance_result": result,
            "status": "pending_approval",
            "escalation": {
                "parent_agent": AGENT_NAME,
                "child_agent": "report_agent",
                "requested_scope": requested_scope,
                "available_scope": token.scope,
                "reason": str(exc),
            },
            "token": token.encoded,
            "scope": token.scope,
        }

    return {
        **state,
        "finance_result": result,
        "token": delegated_token.encoded,
        "scope": delegated_token.scope,
    }