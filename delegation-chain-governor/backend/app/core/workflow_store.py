"""
Lightweight in-memory workflow registry.

Tracks the latest known state of each in-flight/completed request so that
GET /api/workflow/{request_id} has something to return without requiring a
round trip through LangGraph checkpointing. The durable, queryable record of
delegation hops lives in Postgres (`delegation_logs`, `execution_logs`) via
app.core.audit -- this store is just a fast-path cache.
"""

from __future__ import annotations

import threading
from typing import Any

_lock = threading.Lock()
_workflows: dict[str, dict[str, Any]] = {}


def create(request_id: str, query: str) -> None:
    with _lock:
        _workflows[request_id] = {
            "request_id": request_id,
            "query": query,
            "status": "running",
            "current_agent": "gateway_agent",
            "plan": None,
            "finance_result": None,
            "report_result": None,
            "error": None,
            "escalation": None,   # NEW
            "note": None,  
        }


def update(request_id: str, **fields: Any) -> None:
    with _lock:
        if request_id in _workflows:
            _workflows[request_id].update(fields)


def get(request_id: str) -> dict[str, Any] | None:
    with _lock:
        return _workflows.get(request_id)
