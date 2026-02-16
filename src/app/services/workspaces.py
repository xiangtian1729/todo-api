from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_membership import WorkspaceMembership
from app.schemas.workspace import (
    RoleEnum,
    WorkspaceCreate,
    WorkspaceMemberCreate,
    WorkspaceMemberUpdate,
)
from app.services.audit import log_action
from app.services.permissions import (
    count_role_members,
    require_workspace_membership,
    require_workspace_role,
)


def _workspace_payload(workspace: Workspace, role: str) -> dict:
    return {
        "id": workspace.id,
        "name": workspace.name,
        "created_by": workspace.created_by,
        "created_at": workspace.created_at,
        "updated_at": workspace.updated_at,
        "role": role,
    }


async def create_workspace(
    db: AsyncSession,
    *,
    actor_user_id: int,
    data: WorkspaceCreate,
) -> dict:
    workspace = Workspace(name=data.name, created_by=actor_user_id)
    db.add(workspace)
    await db.flush()

    membership = WorkspaceMembership(
        workspace_id=workspace.id,
        user_id=actor_user_id,
        role=RoleEnum.owner.value,
    )
    db.add(membership)

    await log_action(
        db,
        actor_user_id=actor_user_id,
        workspace_id=workspace.id,
        entity_type="workspace",
        entity_id=workspace.id,
        action="create",
        changes={"name": data.name},
    )

    await db.commit()
    await db.refresh(workspace)
    return _workspace_payload(workspace, membership.role)


async def list_workspaces(db: AsyncSession, *, user_id: int) -> list[dict]:
    result = await db.execute(
        select(Workspace, WorkspaceMembership.role)
        .join(WorkspaceMembership, WorkspaceMembership.workspace_id == Workspace.id)
        .where(WorkspaceMembership.user_id == user_id)
        .order_by(Workspace.created_at.desc(), Workspace.id.desc())
    )
    rows = result.all()
    return [_workspace_payload(workspace, role) for workspace, role in rows]


async def get_workspace(db: AsyncSession, *, workspace_id: int, user_id: int) -> dict:
    membership = await require_workspace_membership(db, workspace_id, user_id)
    result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    workspace = result.scalar_one_or_none()
    if workspace is None:
        raise NotFoundError("Workspace not found")
    return _workspace_payload(workspace, membership.role)


async def list_workspace_members(
    db: AsyncSession,
    *,
    workspace_id: int,
    actor_user_id: int,
) -> list[dict]:
    """List all members of a workspace with their usernames."""
    await require_workspace_membership(db, workspace_id, actor_user_id)

    result = await db.execute(
        select(WorkspaceMembership, User.username)
        .join(User, User.id == WorkspaceMembership.user_id)
        .where(WorkspaceMembership.workspace_id == workspace_id)
        .order_by(WorkspaceMembership.created_at.asc())
    )
    rows = result.all()
    return [
        {
            "user_id": membership.user_id,
            "username": username,
            "role": membership.role,
            "created_at": membership.created_at,
            "updated_at": membership.updated_at,
        }
        for membership, username in rows
    ]


async def add_workspace_member(
    db: AsyncSession,
    *,
    workspace_id: int,
    actor_user_id: int,
    data: WorkspaceMemberCreate,
) -> WorkspaceMembership:
    actor_membership = await require_workspace_role(
        db,
        workspace_id,
        actor_user_id,
        allowed_roles={RoleEnum.owner.value, RoleEnum.admin.value},
    )

    if actor_membership.role == RoleEnum.admin.value and data.role == RoleEnum.owner:
        raise ForbiddenError("Only owner can grant owner role")

    user_result = await db.execute(select(User.id).where(User.id == data.user_id))
    if user_result.scalar_one_or_none() is None:
        raise NotFoundError("User not found")

    existing = await db.execute(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == data.user_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError("User already in workspace")

    membership = WorkspaceMembership(
        workspace_id=workspace_id,
        user_id=data.user_id,
        role=data.role.value,
    )
    db.add(membership)

    await log_action(
        db,
        actor_user_id=actor_user_id,
        workspace_id=workspace_id,
        entity_type="workspace_membership",
        entity_id=data.user_id,
        action="create",
        changes={"role": data.role.value},
    )

    try:
        await db.commit()
    except IntegrityError as err:
        await db.rollback()
        raise ConflictError("User already in workspace") from err

    await db.refresh(membership)
    return membership


async def update_workspace_member(
    db: AsyncSession,
    *,
    workspace_id: int,
    actor_user_id: int,
    target_user_id: int,
    data: WorkspaceMemberUpdate,
) -> WorkspaceMembership:
    actor_membership = await require_workspace_role(
        db,
        workspace_id,
        actor_user_id,
        allowed_roles={RoleEnum.owner.value, RoleEnum.admin.value},
    )

    result = await db.execute(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == target_user_id,
        )
    )
    target = result.scalar_one_or_none()
    if target is None:
        raise NotFoundError("Member not found")

    if actor_membership.role == RoleEnum.admin.value and (
        target.role == RoleEnum.owner.value or data.role == RoleEnum.owner
    ):
        raise ForbiddenError("Only owner can update owner role")

    if target.role == RoleEnum.owner.value and data.role != RoleEnum.owner:
        owner_count = await count_role_members(db, workspace_id, RoleEnum.owner.value)
        if owner_count <= 1:
            raise BadRequestError("Cannot demote the last owner")

    previous_role = target.role
    target.role = data.role.value

    await log_action(
        db,
        actor_user_id=actor_user_id,
        workspace_id=workspace_id,
        entity_type="workspace_membership",
        entity_id=target_user_id,
        action="update_role",
        changes={"from": previous_role, "to": data.role.value},
    )

    await db.commit()
    await db.refresh(target)
    return target


async def remove_workspace_member(
    db: AsyncSession,
    *,
    workspace_id: int,
    actor_user_id: int,
    target_user_id: int,
) -> None:
    actor_membership = await require_workspace_role(
        db,
        workspace_id,
        actor_user_id,
        allowed_roles={RoleEnum.owner.value, RoleEnum.admin.value},
    )

    result = await db.execute(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == target_user_id,
        )
    )
    target = result.scalar_one_or_none()
    if target is None:
        raise NotFoundError("Member not found")

    if actor_membership.role == RoleEnum.admin.value and target.role == RoleEnum.owner.value:
        raise ForbiddenError("Only owner can remove an owner")

    if target.role == RoleEnum.owner.value:
        owner_count = await count_role_members(db, workspace_id, RoleEnum.owner.value)
        if owner_count <= 1:
            raise BadRequestError("Cannot remove the last owner")

    await log_action(
        db,
        actor_user_id=actor_user_id,
        workspace_id=workspace_id,
        entity_type="workspace_membership",
        entity_id=target_user_id,
        action="delete",
        changes={"role": target.role},
    )

    await db.delete(target)
    await db.commit()
