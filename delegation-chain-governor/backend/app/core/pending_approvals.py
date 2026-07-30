"""
In-memory store for workflows paused on a scope-escalation decision.

When the Governor blocks a delegation, the workflow halts instead of
crashing. The full state needed to resume it (or gracefully finish without
the blocked step) is kept here until the user calls
POST /api/workflow/{request_id}/resolve.
"""

from __future__ import annotations

import threading
from typing import Any

_lock = threading.Lock()
_pending: dict[str, dict[str, Any]] = {}


def save(request_id: str, state: dict[str, Any]) -> None:
    with _lock:
        _pending[request_id] = state


def pop(request_id: str) -> dict[str, Any] | None:
    with _lock:
        return _pending.pop(request_id, None)


def peek(request_id: str) -> dict[str, Any] | None:
    with _lock:
        return _pending.get(request_id)