from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, NotFoundError
from app.models.task import Task
from app.models.task_tag import TaskTag
from app.schemas.comment import TagCreate
from app.services.audit import log_action
from app.services.permissions import require_workspace_membership


async def _require_task(
    db: AsyncSession,
    *,
    workspace_id: int,
    task_id: int,
) -> Task:
    result = await db.execute(
        select(Task).where(
            Task.workspace_id == workspace_id,
            Task.id == task_id,
        )
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise NotFoundError("Task not found")
    return task


async def add_tag(
    db: AsyncSession,
    *,
    workspace_id: int,
    task_id: int,
    actor_user_id: int,
    data: TagCreate,
) -> TaskTag:
    await require_workspace_membership(db, workspace_id, actor_user_id)
    await _require_task(db, workspace_id=workspace_id, task_id=task_id)

    tag = TaskTag(task_id=task_id, tag=data.tag)
    db.add(tag)

    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise ConflictError("Tag already exists for this task")

    await log_action(
        db,
        actor_user_id=actor_user_id,
        workspace_id=workspace_id,
        entity_type="task_tag",
        entity_id=tag.id,
        action="create",
        changes={"tag": data.tag, "task_id": task_id},
    )

    await db.commit()
    await db.refresh(tag)
    return tag


async def delete_tag(
    db: AsyncSession,
    *,
    workspace_id: int,
    task_id: int,
    tag_value: str,
    actor_user_id: int,
) -> None:
    await require_workspace_membership(db, workspace_id, actor_user_id)
    await _require_task(db, workspace_id=workspace_id, task_id=task_id)

    result = await db.execute(
        select(TaskTag).where(
            TaskTag.task_id == task_id,
            TaskTag.tag == tag_value,
        )
    )
    tag = result.scalar_one_or_none()
    if tag is None:
        raise NotFoundError("Tag not found")

    await log_action(
        db,
        actor_user_id=actor_user_id,
        workspace_id=workspace_id,
        entity_type="task_tag",
        entity_id=tag.id,
        action="delete",
        changes={"tag": tag_value, "task_id": task_id},
    )

    await db.delete(tag)
    await db.commit()
