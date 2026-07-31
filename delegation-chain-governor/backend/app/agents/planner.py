"""
Planner Agent.

Receives a delegated token from the Gateway Agent, produces an execution
plan, and prepares (but does not directly call) the reduced-scope tokens
that the Finance and Report agents will need. All handoffs still go
through the Governor -- the Planner never talks to Finance/Report directly.
"""

from __future__ import annotations

from app.agents.llm import complete
from app.agents.state import DelegationState
from app.core.governor import governor

AGENT_NAME = "planner_agent"

SYSTEM_PROMPT = (
    "You are the Planner Agent in a secured multi-agent finance workflow. "
    "Given a user query, produce a short, numbered execution plan describing "
    "what the Finance Agent should compute and what the Report Agent should "
    "summarize. Be concise."
)


async def run(state: DelegationState) -> DelegationState:
    parent_token = governor.verify(state["token"])

    plan = await complete(SYSTEM_PROMPT, state["query"])

    # Delegate a reduced scope forward -- Planner never grants more than it holds.
    delegated_token = governor.delegate(
        parent_token=parent_token,
        child_agent="finance_agent",
        requested_scope=["finance:read", "finance:report"],
    )

    return {
        **state,
        "plan": plan,
        "token": delegated_token.encoded,
        "scope": delegated_token.scope,
        "token_chain": [*state.get("token_chain", []), governor.to_public_dict(delegated_token)],
    }
