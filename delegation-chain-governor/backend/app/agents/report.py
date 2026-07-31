from __future__ import annotations

from app.agents.llm import complete
from app.agents.state import DelegationState
from app.core.governor import ScopePermissionError, governor

AGENT_NAME = "report_agent"
REQUIRED_SCOPE = "report:generate"

SYSTEM_PROMPT = (
    "You are the Report Agent. Combine the plan and finance findings into a "
    "clear, well-structured final report for the end user."
)


async def run(state: DelegationState) -> DelegationState:
    token = governor.verify(state["token"])

    try:
        governor.enforce(token, REQUIRED_SCOPE)
    except ScopePermissionError as exc:
        return {**state, "status": "failed", "error": str(exc)}

    combined_input = (
        f"Plan:\n{state.get('plan', '')}\n\n"
        f"Finance findings:\n{state.get('finance_result', '')}"
    )
    result = await complete(SYSTEM_PROMPT, combined_input)

    return {**state, "report_result": result, "status": "completed"}