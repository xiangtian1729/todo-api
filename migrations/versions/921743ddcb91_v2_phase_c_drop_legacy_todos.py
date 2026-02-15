"""v2 phase c drop legacy todos

Revision ID: 921743ddcb91
Revises: 75d651717369
Create Date: 2026-02-15 17:20:11.724160
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "921743ddcb91"
down_revision = "75d651717369"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_todos_user_created_at", table_name="todos")
    op.drop_index("ix_todos_user_id", table_name="todos")
    op.drop_table("todos")


def downgrade() -> None:
    op.create_table(
        "todos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_completed", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("priority", sa.Integer(), server_default=sa.text("2"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_todos_user_id", "todos", ["user_id"], unique=False)
    op.create_index(
        "ix_todos_user_created_at",
        "todos",
        ["user_id", "created_at"],
        unique=False,
    )
