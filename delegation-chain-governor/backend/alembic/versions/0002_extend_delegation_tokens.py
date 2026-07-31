"""extend delegation_tokens with task_id, agent, origin_user, max_scope, depth

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-31
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "delegation_tokens",
        "parent_token",
        type_=sa.Text(),
        postgresql_using="parent_token::text",
    )
    op.add_column("delegation_tokens", sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("delegation_tokens", sa.Column("agent", sa.Text(), nullable=True))
    op.add_column("delegation_tokens", sa.Column("origin_user", sa.Text(), nullable=True))
    op.add_column("delegation_tokens", sa.Column("max_scope", sa.Text(), nullable=True))
    op.add_column("delegation_tokens", sa.Column("depth", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("delegation_tokens", "depth")
    op.drop_column("delegation_tokens", "max_scope")
    op.drop_column("delegation_tokens", "origin_user")
    op.drop_column("delegation_tokens", "agent")
    op.drop_column("delegation_tokens", "task_id")
    op.alter_column(
        "delegation_tokens",
        "parent_token",
        type_=postgresql.UUID(as_uuid=True),
        postgresql_using="parent_token::uuid",
    )