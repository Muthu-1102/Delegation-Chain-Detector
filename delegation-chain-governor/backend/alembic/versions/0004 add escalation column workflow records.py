"""add missing escalation column to workflow_records

The `workflow_records` table on some databases was created (or stamped as
created) before the `escalation` JSONB column existed in the model /
migration 0003. Because those databases already have their
`alembic_version` pointer at "0003", re-running `alembic upgrade head`
does not retroactively re-apply 0003's body, so the column never gets
created and every insert into `workflow_records` from
`app.core.workflow_store.create()` fails with:

    asyncpg.exceptions.UndefinedColumnError: column "escalation" of
    relation "workflow_records" does not exist

This migration is idempotent (checks for column existence first) so it is
safe to run both on databases that are missing the column and on fresh
databases where 0003 already created it correctly.

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-31
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    if not _has_column("workflow_records", "escalation"):
        op.add_column(
            "workflow_records",
            sa.Column("escalation", postgresql.JSONB, nullable=True),
        )


def downgrade() -> None:
    if _has_column("workflow_records", "escalation"):
        op.drop_column("workflow_records", "escalation")