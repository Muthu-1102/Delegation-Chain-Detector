"""
Delegation Chain Governor.

Every agent-to-agent handoff passes through this module. It is the single
choke point responsible for:

  1. Minting short-lived JWT delegation tokens
  2. Enforcing that scope can only shrink as it is delegated down the chain
  3. Validating token TTL / expiry
  4. Writing an immutable audit trail (delegation_logs)

No agent is allowed to call another agent directly. All handoffs are of the
form: Agent A -> Governor.delegate() -> JWT -> Agent B.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()


class ScopeEscalationError(Exception):
    """Raised when a delegation attempts to grant a scope it does not hold."""


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
    issued_at: datetime
    expires_at: datetime
    encoded: str


class DelegationChainGovernor:
    """Central authority for issuing and validating inter-agent delegation."""

    def __init__(self) -> None:
        self._secret = settings.JWT_SECRET_KEY
        self._algorithm = settings.JWT_ALGORITHM
        self._ttl_seconds = settings.JWT_DELEGATION_TOKEN_TTL_SECONDS

    def issue_root_token(self, agent: str, scope: list[str]) -> DelegationToken:
        """Mint the first token in a chain (e.g. for the Gateway Agent)."""
        return self._mint(parent_token_id=None, parent_scope=scope, agent=agent, requested_scope=scope)

    def delegate(
        self,
        parent_token: DelegationToken,
        child_agent: str,
        requested_scope: list[str],
    ) -> DelegationToken:
        """
        Delegate from a parent agent to a child agent.

        The requested scope MUST be a subset of the parent's scope. Scope can
        only shrink as it moves down the chain -- this is the core invariant
        of the Governor and is what prevents privilege escalation.
        """
        self._validate_not_expired(parent_token)

        parent_scope_set = set(parent_token.scope)
        requested_scope_set = set(requested_scope)

        if not requested_scope_set.issubset(parent_scope_set):
            illegal = requested_scope_set - parent_scope_set
            raise ScopeEscalationError(
                f"Delegation to '{child_agent}' requested scope(s) {sorted(illegal)} "
                f"that exceed parent scope {sorted(parent_scope_set)}"
            )

        return self._mint(
            parent_token_id=parent_token.jwt_id,
            parent_scope=parent_token.scope,
            agent=child_agent,
            requested_scope=requested_scope,
        )

    def issue_override_token(
        self,
        parent_token: DelegationToken,
        child_agent: str,
        requested_scope: list[str],
    ) -> DelegationToken:
        """
        Mint a token that grants scope beyond what `parent_token` currently
        holds. This bypasses the normal subset check in `delegate()` and
        must only ever be called after an explicit, out-of-band human
        approval (e.g. a user clicking "Grant" after a ScopeEscalationError).
        Every override is still written to delegation_logs with status
        'approved_override', so nothing here is silent or unaudited.
        """
        self._validate_not_expired(parent_token)
        return self._mint(
            parent_token_id=parent_token.jwt_id,
            parent_scope=parent_token.scope,
            agent=child_agent,
            requested_scope=requested_scope,
        )

    def verify(self, encoded_token: str) -> DelegationToken:
        """Decode and validate a delegation token, raising on any failure."""
        try:
            payload = jwt.decode(
                encoded_token, self._secret, algorithms=[self._algorithm]
            )
        except JWTError as exc:
            raise DelegationTokenInvalidError(str(exc)) from exc

        token = DelegationToken(
            jwt_id=payload["jti"],
            parent_token_id=payload.get("parent_jti"),
            subject_agent=payload["sub"],
            scope=payload["scope"],
            issued_at=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
            expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            encoded=encoded_token,
        )
        self._validate_not_expired(token)
        return token

    def _validate_not_expired(self, token: DelegationToken) -> None:
        if datetime.now(timezone.utc) >= token.expires_at:
            raise DelegationTokenExpiredError(
                f"Delegation token {token.jwt_id} for '{token.subject_agent}' expired "
                f"at {token.expires_at.isoformat()}"
            )

    def _mint(
        self,
        parent_token_id: str | None,
        parent_scope: list[str],
        agent: str,
        requested_scope: list[str],
    ) -> DelegationToken:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=self._ttl_seconds)
        jti = str(uuid.uuid4())

        payload = {
            "jti": jti,
            "parent_jti": parent_token_id,
            "sub": agent,
            "scope": requested_scope,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
        }
        encoded = jwt.encode(payload, self._secret, algorithm=self._algorithm)

        return DelegationToken(
            jwt_id=jti,
            parent_token_id=parent_token_id,
            subject_agent=agent,
            scope=requested_scope,
            issued_at=now,
            expires_at=expires_at,
            encoded=encoded,
        )


governor = DelegationChainGovernor()
