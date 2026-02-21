from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, NotFoundError
from app.models.task import Task
from app.models.task_watcher import TaskWatcher
from app.schemas.comment import WatcherCreate
from app.services.audit import log_action
from app.services.permissions import ensure_user_in_workspace, require_workspace_membership


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


async def list_watchers(
    db: AsyncSession,
    *,
    workspace_id: int,
    task_id: int,
    actor_user_id: int,
) -> list[TaskWatcher]:
    await require_workspace_membership(db, workspace_id, actor_user_id)
    await _require_task(db, workspace_id=workspace_id, task_id=task_id)
    result = await db.execute(select(TaskWatcher).where(TaskWatcher.task_id == task_id))
    return list(result.scalars().all())


async def add_watcher(
    db: AsyncSession,
    *,
    workspace_id: int,
    task_id: int,
    actor_user_id: int,
    data: WatcherCreate,
) -> TaskWatcher:
    await require_workspace_membership(db, workspace_id, actor_user_id)
    await _require_task(db, workspace_id=workspace_id, task_id=task_id)
    await ensure_user_in_workspace(db, workspace_id, data.user_id)

    watcher = TaskWatcher(task_id=task_id, user_id=data.user_id)
    db.add(watcher)

    try:
        await db.flush()
    except IntegrityError as err:
        await db.rollback()
        raise ConflictError("Watcher already exists for this task") from err

    await log_action(
        db,
        actor_user_id=actor_user_id,
        workspace_id=workspace_id,
        entity_type="task_watcher",
        entity_id=watcher.id,
        action="create",
        changes={"task_id": task_id, "user_id": data.user_id},
    )

    await db.commit()
    await db.refresh(watcher)
    return watcher


async def delete_watcher(
    db: AsyncSession,
    *,
    workspace_id: int,
    task_id: int,
    watcher_user_id: int,
    actor_user_id: int,
) -> None:
    await require_workspace_membership(db, workspace_id, actor_user_id)
    await _require_task(db, workspace_id=workspace_id, task_id=task_id)

    result = await db.execute(
        select(TaskWatcher).where(
            TaskWatcher.task_id == task_id,
            TaskWatcher.user_id == watcher_user_id,
        )
    )
    watcher = result.scalar_one_or_none()
    if watcher is None:
        raise NotFoundError("Watcher not found")

    await log_action(
        db,
        actor_user_id=actor_user_id,
        workspace_id=workspace_id,
        entity_type="task_watcher",
        entity_id=watcher.id,
        action="delete",
        changes={"task_id": task_id, "user_id": watcher_user_id},
    )

    await db.delete(watcher)
    await db.commit()
