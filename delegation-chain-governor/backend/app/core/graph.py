"""
LangGraph orchestration.

Builds the agent execution graph:

    gateway_agent -> planner_agent -> finance_agent -> report_agent

Each transition corresponds to a Governor-mediated delegation. Conditional
routing short-circuits to END as soon as any node sets status="failed" (e.g.
a scope check failure), so a rejected delegation never reaches a downstream
agent.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.agents import finance, gateway, planner, report
from app.agents.state import DelegationState


def _route_after(node_name: str):
    def _router(state: DelegationState) -> str:
        if state.get("status") in ("failed", "pending_approval"):
            return END
        return node_name

    return _router


def build_graph():
    graph = StateGraph(DelegationState)

    graph.add_node("gateway_agent", gateway.run)
    graph.add_node("planner_agent", planner.run)
    graph.add_node("finance_agent", finance.run)
    graph.add_node("report_agent", report.run)

    graph.set_entry_point("gateway_agent")

    graph.add_conditional_edges("gateway_agent", _route_after("planner_agent"))
    graph.add_conditional_edges("planner_agent", _route_after("finance_agent"))
    graph.add_conditional_edges("finance_agent", _route_after("report_agent"))
    graph.add_edge("report_agent", END)

    return graph.compile()


compiled_graph = build_graph()


async def run_workflow(request_id: str, query: str, origin_user: str = "anonymous") -> DelegationState:
    initial_state: DelegationState = {
        "request_id": request_id,
        "origin_user": origin_user,
        "query": query,
        "status": "running",
        "error": None,
        "token_chain": [],
    }
    final_state: DelegationState = await compiled_graph.ainvoke(initial_state)
    return final_state