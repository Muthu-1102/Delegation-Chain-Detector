from __future__ import annotations

from app.agents.state import DelegationState
from app.core.governor import governor

AGENT_NAME = "gateway_agent"


async def run(state: DelegationState) -> DelegationState:
    root_token = governor.issue_root_token(
        agent=AGENT_NAME,
        scope=["finance:read", "finance:report", "report:generate"],
        task_id=state["request_id"],
        origin_user=state.get("origin_user", "anonymous"),
    )

    return {
        **state,
        "token": root_token.encoded,
        "scope": root_token.scope,
        "status": "running",
        "token_chain": [governor.to_public_dict(root_token)],
    }