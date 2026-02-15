from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ForbiddenError, NotFoundError
from app.models.workspace_membership import WorkspaceMembership

ADMIN_ROLES = {"owner", "admin"}


async def get_workspace_membership(
    db: AsyncSession,
    workspace_id: int,
    user_id: int,
) -> WorkspaceMembership | None:
    result = await db.execute(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def require_workspace_membership(
    db: AsyncSession,
    workspace_id: int,
    user_id: int,
) -> WorkspaceMembership:
    membership = await get_workspace_membership(db, workspace_id, user_id)
    if membership is None:
        raise NotFoundError("Workspace not found")
    return membership


async def require_workspace_role(
    db: AsyncSession,
    workspace_id: int,
    user_id: int,
    allowed_roles: set[str],
) -> WorkspaceMembership:
    membership = await require_workspace_membership(db, workspace_id, user_id)
    if membership.role not in allowed_roles:
        raise ForbiddenError("Insufficient permissions")
    return membership


async def ensure_user_in_workspace(
    db: AsyncSession,
    workspace_id: int,
    user_id: int,
) -> WorkspaceMembership:
    membership = await get_workspace_membership(db, workspace_id, user_id)
    if membership is None:
        raise NotFoundError("User not in workspace")
    return membership


async def count_role_members(
    db: AsyncSession,
    workspace_id: int,
    role: str,
) -> int:
    from sqlalchemy import func

    result = await db.execute(
        select(func.count(WorkspaceMembership.id)).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.role == role,
        )
    )
    return int(result.scalar_one())


def is_owner_or_admin(role: str) -> bool:
    return role in ADMIN_ROLES
