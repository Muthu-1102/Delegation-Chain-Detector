"""Pydantic request/response models, matching docs/API_SPEC.md."""

from __future__ import annotations

from pydantic import BaseModel
from typing import Literal 

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class QueryRequest(BaseModel):
    query: str
    user: str = "anonymous"


class QueryResponse(BaseModel):
    request_id: str
    status: str


class EscalationInfo(BaseModel):
    parent_agent: str
    child_agent: str
    requested_scope: list[str]
    available_scope: list[str]
    reason: str


class ResolveDecisionRequest(BaseModel):
    decision: Literal["grant", "deny"]

class WorkflowStatusResponse(BaseModel):
    request_id: str
    status: str
    current_agent: str | None = None
    plan: str | None = None
    finance_result: str | None = None
    report_result: str | None = None
    error: str | None = None
    escalation: EscalationInfo | None = None
    note: str | None = None


class DelegationLogEntry(BaseModel):
    parent_agent: str
    child_agent: str
    delegated_scope: str
    status: str
    timestamp: str


class TokenChainEntry(BaseModel):
    agent: str
    parent_agent: str | None
    scope: list[str]
    max_scope: list[str]
    depth: int
    origin_user: str
    issued_at: str
    expires_at: str


class AuditResponse(BaseModel):
    request_id: str
    chain: list[TokenChainEntry]
    decisions: list[DelegationLogEntry]


class ExecutionLogEntry(BaseModel):
    request_id: str
    agent: str
    execution_time: float
    status: str
    message: str


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "delegation-chain-governor"