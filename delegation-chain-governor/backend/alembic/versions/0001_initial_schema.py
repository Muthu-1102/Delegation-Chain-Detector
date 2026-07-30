"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text, nullable=False),
    )

    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("scope", sa.Text, nullable=False),
    )

    op.create_table(
        "delegation_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("parent_token", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("jwt_id", sa.Text, nullable=False, unique=True),
        sa.Column("scope", sa.Text, nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "delegation_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_agent", sa.Text, nullable=False),
        sa.Column("child_agent", sa.Text, nullable=False),
        sa.Column("delegated_scope", sa.Text, nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "execution_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent", sa.Text, nullable=False),
        sa.Column("execution_time", sa.Float, nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("message", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("execution_logs")
    op.drop_table("delegation_logs")
    op.drop_table("delegation_tokens")
    op.drop_table("permissions")
    op.drop_table("users")
