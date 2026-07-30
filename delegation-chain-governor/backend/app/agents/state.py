"""Shared LangGraph state passed between agent nodes."""

from __future__ import annotations

from typing import TypedDict


class DelegationState(TypedDict, total=False):
    request_id: str
    query: str
    token: str          # currently-held delegation JWT (encoded)
    scope: list[str]     # scope carried by `token`
    plan: str
    finance_result: str
    report_result: str
    status: str          # "running" | "completed" | "failed"
    error: str | None
    escalation: dict | None  
    note: str | None    