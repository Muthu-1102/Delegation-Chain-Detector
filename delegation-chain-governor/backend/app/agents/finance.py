from __future__ import annotations

from app.agents.llm import complete
from app.agents.state import DelegationState
from app.core.governor import ScopeEscalationError, ScopePermissionError, governor

AGENT_NAME = "finance_agent"
REQUIRED_SCOPE = "finance:read"

SYSTEM_PROMPT = (
    "You are the Finance Agent. Given a plan, produce a concise financial "
    "analysis or figures relevant to the request. Do not fabricate exact "
    "real-world data; clearly mark illustrative figures as such."
)


async def run(state: DelegationState) -> DelegationState:
    token = governor.verify(state["token"])

    try:
        governor.enforce(token, REQUIRED_SCOPE)
    except ScopePermissionError as exc:
        return {**state, "status": "failed", "error": str(exc)}

    result = await complete(SYSTEM_PROMPT, state["plan"])
    requested_scope = ["report:generate"]

    try:
        delegated_token = governor.delegate(
            parent_token=token,
            child_agent="report_agent",
            requested_scope=requested_scope,
        )
    except ScopeEscalationError as exc:
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
        "token_chain": [*state.get("token_chain", []), governor.to_public_dict(delegated_token)],
    }