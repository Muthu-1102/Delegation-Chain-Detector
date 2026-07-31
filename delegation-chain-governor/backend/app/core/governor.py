"""
Delegation Chain Governor.

Every agent-to-agent handoff passes through this module. Per PS-2.3, each
signed delegation token carries:

  - jti / parent_jti   : this token's id, and the id of the token it was derived from
  - sub                : the agent this token was issued to
  - scope               : the scope THIS hop actually holds
  - task_id             : the originating task / request id
  - origin_user         : the user who triggered the task
  - max_scope           : the scope granted at the ROOT of the chain -- an
                           absolute ceiling that no descendant token, no
                           matter how many hops deep, may ever exceed
  - depth               : how many hops from the root this token is
  - iat / exp            : issued-at / expiry (TTL enforced on every use)

Two independent checks guard against scope expansion:
  1. `delegate()` requires the requested scope to be a subset of the
     immediate PARENT's scope (this is what stops Agent B from handing
     Agent C something Agent B itself doesn't hold).
  2. `delegate()` (and `issue_override_token()`) ALSO require the requested
     scope to be a subset of `max_scope`, the scope granted at task
     creation. This is defense-in-depth: even if check #1 were ever buggy
     or bypassed at one hop, no token for this task can ever carry more
     authority than the user originally granted it.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()


class ScopeEscalationError(Exception):
    """Raised when a delegation attempts to grant scope it does not hold,
    or scope beyond the task's original max_scope ceiling."""


class ScopePermissionError(Exception):
    """Raised by the enforcement interceptor when a token's scope does not
    permit the tool call an agent is about to make."""


class DelegationTokenExpiredError(Exception):
    """Raised when a delegation token has expired."""


class DelegationTokenInvalidError(Exception):
    """Raised when a delegation token fails signature / structure validation."""


@dataclass
class DelegationToken:
    jwt_id: str
    parent_token_id: str | None
    subject_agent: str
    scope: list[str]
    task_id: str
    origin_user: str
    max_scope: list[str]
    depth: int
    issued_at: datetime
    expires_at: datetime
    encoded: str


class DelegationChainGovernor:
    """Central authority for issuing, validating, and enforcing delegation."""

    def __init__(self) -> None:
        self._secret = settings.JWT_SECRET_KEY
        self._algorithm = settings.JWT_ALGORITHM
        self._ttl_seconds = settings.JWT_DELEGATION_TOKEN_TTL_SECONDS

    def issue_root_token(
        self, agent: str, scope: list[str], task_id: str, origin_user: str = "anonymous"
    ) -> DelegationToken:
        """Mint the first token in a chain. The root's scope IS the task's
        max_scope ceiling -- nothing downstream can ever exceed this."""
        return self._mint(
            parent_token_id=None,
            agent=agent,
            requested_scope=scope,
            task_id=task_id,
            origin_user=origin_user,
            max_scope=scope,
            depth=0,
        )

    def delegate(
        self,
        parent_token: DelegationToken,
        child_agent: str,
        requested_scope: list[str],
    ) -> DelegationToken:
        """
        Delegate from a parent agent to a child agent. Requested scope must
        be a subset of BOTH the immediate parent's scope AND the task's
        max_scope ceiling.
        """
        self._validate_not_expired(parent_token)
        self._validate_subset(requested_scope, parent_token.scope, child_agent, "parent scope")
        self._validate_subset(requested_scope, parent_token.max_scope, child_agent, "task max_scope")

        return self._mint(
            parent_token_id=parent_token.jwt_id,
            agent=child_agent,
            requested_scope=requested_scope,
            task_id=parent_token.task_id,
            origin_user=parent_token.origin_user,
            max_scope=parent_token.max_scope,
            depth=parent_token.depth + 1,
        )

    def issue_override_token(
        self,
        parent_token: DelegationToken,
        child_agent: str,
        requested_scope: list[str],
    ) -> DelegationToken:
        """
        Mint a token that may exceed the immediate parent's current scope --
        used only after an explicit, out-of-band human approval (e.g. a user
        clicking "Grant" after a ScopeEscalationError). This still can NEVER
        exceed the task's max_scope: a human can restore scope that an
        earlier hop chose to narrow, but can never grant the task more
        authority than the user originally approved.
        """
        self._validate_not_expired(parent_token)
        self._validate_subset(requested_scope, parent_token.max_scope, child_agent, "task max_scope")

        return self._mint(
            parent_token_id=parent_token.jwt_id,
            agent=child_agent,
            requested_scope=requested_scope,
            task_id=parent_token.task_id,
            origin_user=parent_token.origin_user,
            max_scope=parent_token.max_scope,
            depth=parent_token.depth + 1,
        )

    def enforce(self, token: DelegationToken, required_scope: str) -> None:
        """
        The enforcement interceptor. Call this immediately before an agent
        performs any tool call / protected operation. Raises
        ScopePermissionError if the token's scope does not permit it.
        """
        self._validate_not_expired(token)
        if required_scope not in token.scope:
            raise ScopePermissionError(
                f"'{token.subject_agent}' attempted an operation requiring "
                f"'{required_scope}' but its token only grants {sorted(token.scope)}"
            )

    def verify(self, encoded_token: str) -> DelegationToken:
        """Decode and validate a delegation token, raising on any failure."""
        try:
            payload = jwt.decode(encoded_token, self._secret, algorithms=[self._algorithm])
        except JWTError as exc:
            raise DelegationTokenInvalidError(str(exc)) from exc

        token = DelegationToken(
            jwt_id=payload["jti"],
            parent_token_id=payload.get("parent_jti"),
            subject_agent=payload["sub"],
            scope=payload["scope"],
            task_id=payload["task_id"],
            origin_user=payload["origin_user"],
            max_scope=payload["max_scope"],
            depth=payload["depth"],
            issued_at=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
            expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            encoded=encoded_token,
        )
        self._validate_not_expired(token)
        return token

    def to_public_dict(self, token: DelegationToken) -> dict:
        """JSON-serializable payload snapshot, recorded in agent state so the
        API layer can persist it into `delegation_tokens` -- this is the
        source of truth the audit trail is reconstructed from."""
        return {
            "jwt_id": token.jwt_id,
            "parent_jwt_id": token.parent_token_id,
            "agent": token.subject_agent,
            "scope": token.scope,
            "task_id": token.task_id,
            "origin_user": token.origin_user,
            "max_scope": token.max_scope,
            "depth": token.depth,
            "issued_at": token.issued_at.isoformat(),
            "expires_at": token.expires_at.isoformat(),
        }

    def _validate_subset(
        self, requested: list[str], ceiling: list[str], child_agent: str, ceiling_name: str
    ) -> None:
        requested_set, ceiling_set = set(requested), set(ceiling)
        if not requested_set.issubset(ceiling_set):
            illegal = requested_set - ceiling_set
            raise ScopeEscalationError(
                f"Delegation to '{child_agent}' requested scope(s) {sorted(illegal)} "
                f"that exceed {ceiling_name} {sorted(ceiling_set)}"
            )

    def _validate_not_expired(self, token: DelegationToken) -> None:
        if datetime.now(timezone.utc) >= token.expires_at:
            raise DelegationTokenExpiredError(
                f"Delegation token {token.jwt_id} for '{token.subject_agent}' expired "
                f"at {token.expires_at.isoformat()}"
            )

    def _mint(
        self,
        parent_token_id: str | None,
        agent: str,
        requested_scope: list[str],
        task_id: str,
        origin_user: str,
        max_scope: list[str],
        depth: int,
    ) -> DelegationToken:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=self._ttl_seconds)
        jti = str(uuid.uuid4())

        payload = {
            "jti": jti,
            "parent_jti": parent_token_id,
            "sub": agent,
            "scope": requested_scope,
            "task_id": task_id,
            "origin_user": origin_user,
            "max_scope": max_scope,
            "depth": depth,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
        }
        encoded = jwt.encode(payload, self._secret, algorithm=self._algorithm)

        return DelegationToken(
            jwt_id=jti,
            parent_token_id=parent_token_id,
            subject_agent=agent,
            scope=requested_scope,
            task_id=task_id,
            origin_user=origin_user,
            max_scope=max_scope,
            depth=depth,
            issued_at=now,
            expires_at=expires_at,
            encoded=encoded,
        )


governor = DelegationChainGovernor()