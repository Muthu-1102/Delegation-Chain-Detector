"""
Report Agent.

Final node in the delegation chain. Requires 'report:generate' scope.
Compiles the plan + finance result into a user-facing report and marks
the workflow complete. Holds the narrowest scope of any agent in the chain.
"""

from __future__ import annotations

from app.agents.llm import complete
from app.agents.state import DelegationState
from app.core.governor import governor

AGENT_NAME = "report_agent"
REQUIRED_SCOPE = "report:generate"

SYSTEM_PROMPT = (
    "You are the Report Agent. Combine the plan and finance findings into a "
    "clear, well-structured final report for the end user."
)


async def run(state: DelegationState) -> DelegationState:
    token = governor.verify(state["token"])

    if REQUIRED_SCOPE not in token.scope:
        return {
            **state,
            "status": "failed",
            "error": f"report_agent missing required scope '{REQUIRED_SCOPE}'",
        }

    combined_input = (
        f"Plan:\n{state.get('plan', '')}\n\n"
        f"Finance findings:\n{state.get('finance_result', '')}"
    )
    result = await complete(SYSTEM_PROMPT, combined_input)

    return {
        **state,
        "report_result": result,
        "status": "completed",
    }
