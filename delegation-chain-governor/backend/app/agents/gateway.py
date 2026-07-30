"""
Gateway Agent.

Entry point for every user request. Responsible for:
  - Issuing the root delegation token (full scope granted to the requesting user)
  - Handing the request off to the Planner Agent through the Governor
"""

from __future__ import annotations

from app.agents.state import DelegationState
from app.core.governor import governor

AGENT_NAME = "gateway_agent"


async def run(state: DelegationState) -> DelegationState:
    root_token = governor.issue_root_token(
        agent=AGENT_NAME,
        scope=["finance:read", "finance:report", "report:generate"],
    )

    return {
        **state,
        "token": root_token.encoded,
        "scope": root_token.scope,
        "status": "running",
    }
