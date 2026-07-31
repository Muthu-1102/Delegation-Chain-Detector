from __future__ import annotations
from typing import TypedDict


class DelegationState(TypedDict, total=False):
    request_id: str
    origin_user: str            # NEW
    query: str
    token: str
    scope: list[str]
    plan: str
    finance_result: str
    report_result: str
    status: str
    error: str | None
    escalation: dict | None
    note: str | None
    token_chain: list[dict]     # NEW - every token minted this run, in order