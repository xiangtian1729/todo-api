"""v2 phase b migrate todos to tasks

Revision ID: 75d651717369
Revises: 64acdc31bcad
Create Date: 2026-02-15 17:20:11.372261
"""

from __future__ import annotations

from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "75d651717369"
down_revision = "64acdc31bcad"
branch_labels = None
depends_on = None

LEGACY_WORKSPACE_PREFIX = "__legacy_workspace_u_"
LEGACY_PROJECT_NAME = "__legacy_import_project__"


def _build_tables() -> dict[str, sa.Table]:
    metadata = sa.MetaData()

    return {
        "todos": sa.Table(
            "todos",
            metadata,
            sa.Column("id", sa.Integer),
            sa.Column("user_id", sa.Integer),
            sa.Column("title", sa.String),
            sa.Column("description", sa.Text),
            sa.Column("is_completed", sa.Boolean),
            sa.Column("priority", sa.Integer),
            sa.Column("created_at", sa.DateTime(timezone=True)),
            sa.Column("updated_at", sa.DateTime(timezone=True)),
        ),
        "workspaces": sa.Table(
            "workspaces",
            metadata,
            sa.Column("id", sa.Integer),
            sa.Column("name", sa.String),
            sa.Column("created_by", sa.Integer),
            sa.Column("created_at", sa.DateTime(timezone=True)),
            sa.Column("updated_at", sa.DateTime(timezone=True)),
        ),
        "workspace_memberships": sa.Table(
            "workspace_memberships",
            metadata,
            sa.Column("id", sa.Integer),
            sa.Column("workspace_id", sa.Integer),
            sa.Column("user_id", sa.Integer),
            sa.Column("role", sa.String),
            sa.Column("created_at", sa.DateTime(timezone=True)),
            sa.Column("updated_at", sa.DateTime(timezone=True)),
        ),
        "projects": sa.Table(
            "projects",
            metadata,
            sa.Column("id", sa.Integer),
            sa.Column("workspace_id", sa.Integer),
            sa.Column("name", sa.String),
            sa.Column("description", sa.Text),
            sa.Column("created_by", sa.Integer),
            sa.Column("created_at", sa.DateTime(timezone=True)),
            sa.Column("updated_at", sa.DateTime(timezone=True)),
        ),
        "tasks": sa.Table(
            "tasks",
            metadata,
            sa.Column("id", sa.Integer),
            sa.Column("workspace_id", sa.Integer),
            sa.Column("project_id", sa.Integer),
            sa.Column("title", sa.String),
            sa.Column("description", sa.Text),
            sa.Column("status", sa.String),
            sa.Column("creator_id", sa.Integer),
            sa.Column("assignee_id", sa.Integer),
            sa.Column("due_at", sa.DateTime(timezone=True)),
            sa.Column("version", sa.Integer),
            sa.Column("created_at", sa.DateTime(timezone=True)),
            sa.Column("updated_at", sa.DateTime(timezone=True)),
        ),
    }


def upgrade() -> None:
    bind = op.get_bind()
    tables = _build_tables()

    todos = tables["todos"]
    workspaces = tables["workspaces"]
    memberships = tables["workspace_memberships"]
    projects = tables["projects"]
    tasks = tables["tasks"]

    user_ids = bind.execute(sa.select(sa.distinct(todos.c.user_id))).scalars().all()
    now = datetime.now(UTC)

    for user_id in user_ids:
        workspace_name = f"{LEGACY_WORKSPACE_PREFIX}{user_id}"

        workspace_id = bind.execute(
            sa.select(workspaces.c.id).where(workspaces.c.name == workspace_name)
        ).scalar_one_or_none()

        if workspace_id is None:
            bind.execute(
                workspaces.insert().values(
                    name=workspace_name,
                    created_by=user_id,
                    created_at=now,
                    updated_at=now,
                )
            )
            workspace_id = bind.execute(
                sa.select(workspaces.c.id).where(workspaces.c.name == workspace_name)
            ).scalar_one()

        membership_exists = bind.execute(
            sa.select(memberships.c.id).where(
                memberships.c.workspace_id == workspace_id,
                memberships.c.user_id == user_id,
            )
        ).scalar_one_or_none()
        if membership_exists is None:
            bind.execute(
                memberships.insert().values(
                    workspace_id=workspace_id,
                    user_id=user_id,
                    role="owner",
                    created_at=now,
                    updated_at=now,
                )
            )

        project_id = bind.execute(
            sa.select(projects.c.id).where(
                projects.c.workspace_id == workspace_id,
                projects.c.name == LEGACY_PROJECT_NAME,
            )
        ).scalar_one_or_none()

        if project_id is None:
            bind.execute(
                projects.insert().values(
                    workspace_id=workspace_id,
                    name=LEGACY_PROJECT_NAME,
                    description="Imported from legacy todos",
                    created_by=user_id,
                    created_at=now,
                    updated_at=now,
                )
            )
            project_id = bind.execute(
                sa.select(projects.c.id).where(
                    projects.c.workspace_id == workspace_id,
                    projects.c.name == LEGACY_PROJECT_NAME,
                )
            ).scalar_one()

        todo_rows = bind.execute(
            sa.select(
                todos.c.id,
                todos.c.title,
                todos.c.description,
                todos.c.is_completed,
                todos.c.created_at,
                todos.c.updated_at,
            ).where(todos.c.user_id == user_id)
        ).all()

        for todo_row in todo_rows:
            status = "done" if todo_row.is_completed else "todo"
            bind.execute(
                tasks.insert().values(
                    workspace_id=workspace_id,
                    project_id=project_id,
                    title=todo_row.title,
                    description=todo_row.description,
                    status=status,
                    creator_id=user_id,
                    assignee_id=user_id,
                    due_at=None,
                    version=1,
                    created_at=todo_row.created_at or now,
                    updated_at=todo_row.updated_at or todo_row.created_at or now,
                )
            )


def downgrade() -> None:
    bind = op.get_bind()
    tables = _build_tables()

    workspaces = tables["workspaces"]
    memberships = tables["workspace_memberships"]
    projects = tables["projects"]
    tasks = tables["tasks"]

    legacy_workspace_ids = bind.execute(
        sa.select(workspaces.c.id).where(workspaces.c.name.like(f"{LEGACY_WORKSPACE_PREFIX}%"))
    ).scalars().all()

    if not legacy_workspace_ids:
        return

    legacy_project_ids = bind.execute(
        sa.select(projects.c.id).where(
            projects.c.workspace_id.in_(legacy_workspace_ids),
            projects.c.name == LEGACY_PROJECT_NAME,
        )
    ).scalars().all()

    if legacy_project_ids:
        bind.execute(tasks.delete().where(tasks.c.project_id.in_(legacy_project_ids)))

    bind.execute(
        projects.delete().where(
            projects.c.workspace_id.in_(legacy_workspace_ids),
            projects.c.name == LEGACY_PROJECT_NAME,
        )
    )
    bind.execute(memberships.delete().where(memberships.c.workspace_id.in_(legacy_workspace_ids)))
    bind.execute(workspaces.delete().where(workspaces.c.id.in_(legacy_workspace_ids)))
