from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, NotFoundError
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.schemas.workspace import RoleEnum
from app.services.audit import log_action
from app.services.permissions import require_workspace_membership, require_workspace_role


async def create_project(
    db: AsyncSession,
    *,
    workspace_id: int,
    actor_user_id: int,
    data: ProjectCreate,
) -> Project:
    await require_workspace_role(
        db,
        workspace_id,
        actor_user_id,
        allowed_roles={RoleEnum.owner.value, RoleEnum.admin.value},
    )

    project = Project(
        workspace_id=workspace_id,
        name=data.name,
        description=data.description,
        created_by=actor_user_id,
    )
    db.add(project)
    await db.flush()

    await log_action(
        db,
        actor_user_id=actor_user_id,
        workspace_id=workspace_id,
        entity_type="project",
        entity_id=project.id,
        action="create",
        changes={"name": data.name},
    )

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ConflictError("Project name already exists in workspace")

    await db.refresh(project)
    return project


async def list_projects(
    db: AsyncSession,
    *,
    workspace_id: int,
    user_id: int,
) -> list[Project]:
    await require_workspace_membership(db, workspace_id, user_id)

    result = await db.execute(
        select(Project)
        .where(Project.workspace_id == workspace_id)
        .order_by(Project.created_at.desc(), Project.id.desc())
    )
    return list(result.scalars().all())


async def get_project(
    db: AsyncSession,
    *,
    workspace_id: int,
    project_id: int,
    user_id: int,
) -> Project:
    await require_workspace_membership(db, workspace_id, user_id)

    result = await db.execute(
        select(Project).where(
            Project.workspace_id == workspace_id,
            Project.id == project_id,
        )
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project not found")
    return project


async def update_project(
    db: AsyncSession,
    *,
    workspace_id: int,
    project_id: int,
    actor_user_id: int,
    data: ProjectUpdate,
) -> Project:
    await require_workspace_role(
        db,
        workspace_id,
        actor_user_id,
        allowed_roles={RoleEnum.owner.value, RoleEnum.admin.value},
    )

    result = await db.execute(
        select(Project).where(
            Project.workspace_id == workspace_id,
            Project.id == project_id,
        )
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    await log_action(
        db,
        actor_user_id=actor_user_id,
        workspace_id=workspace_id,
        entity_type="project",
        entity_id=project_id,
        action="update",
        changes=update_data,
    )

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ConflictError("Project name already exists in workspace")

    await db.refresh(project)
    return project


async def delete_project(
    db: AsyncSession,
    *,
    workspace_id: int,
    project_id: int,
    actor_user_id: int,
) -> None:
    await require_workspace_role(
        db,
        workspace_id,
        actor_user_id,
        allowed_roles={RoleEnum.owner.value, RoleEnum.admin.value},
    )

    result = await db.execute(
        select(Project).where(
            Project.workspace_id == workspace_id,
            Project.id == project_id,
        )
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise NotFoundError("Project not found")

    await log_action(
        db,
        actor_user_id=actor_user_id,
        workspace_id=workspace_id,
        entity_type="project",
        entity_id=project_id,
        action="delete",
        changes={"name": project.name},
    )

    await db.delete(project)
    await db.commit()
