"""add workflow_records and pending_approvals tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-31
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workflow_records",
        sa.Column("request_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("query", sa.Text, nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("current_agent", sa.Text, nullable=True),
        sa.Column("plan", sa.Text, nullable=True),
        sa.Column("finance_result", sa.Text, nullable=True),
        sa.Column("report_result", sa.Text, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("escalation", postgresql.JSONB, nullable=True),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "pending_approvals",
        sa.Column("request_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("state", postgresql.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("pending_approvals")
    op.drop_table("workflow_records")