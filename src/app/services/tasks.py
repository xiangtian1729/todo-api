from datetime import datetime

from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.models.project import Project
from app.models.task import Task
from app.models.task_tag import TaskTag
from app.schemas.task import SortOrder, TaskCreate, TaskResponse, TaskSortBy, TaskStatus, TaskStatusTransition, TaskUpdate
from app.services.audit import log_action
from app.services.idempotency import build_request_hash, get_replay_response, save_response
from app.services.permissions import ADMIN_ROLES, ensure_user_in_workspace, require_workspace_membership

ALLOWED_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.todo: {TaskStatus.in_progress},
    TaskStatus.in_progress: {TaskStatus.blocked, TaskStatus.done},
    TaskStatus.blocked: {TaskStatus.in_progress},
    TaskStatus.done: {TaskStatus.in_progress},
}

SORT_COLUMNS = {
    TaskSortBy.created_at: Task.created_at,
    TaskSortBy.updated_at: Task.updated_at,
    TaskSortBy.due_at: Task.due_at,
    TaskSortBy.status: Task.status,
    TaskSortBy.id: Task.id,
}


def _can_manage_task(task: Task, role: str, user_id: int) -> bool:
    if role in ADMIN_ROLES:
        return True
    return task.creator_id == user_id or task.assignee_id == user_id


async def _get_task_scoped(
    db: AsyncSession,
    *,
    workspace_id: int,
    task_id: int,
) -> Task | None:
    result = await db.execute(
        select(Task).where(
            Task.workspace_id == workspace_id,
            Task.id == task_id,
        )
    )
    return result.scalar_one_or_none()


def _apply_task_filters(
    query,
    *,
    status_filter: TaskStatus | None,
    assignee_id: int | None,
    project_id: int | None,
    tag: str | None,
    due_at_from: datetime | None,
    due_at_to: datetime | None,
):
    """将过滤条件统一应用到查询和计数查询上，避免重复构建。"""
    if project_id is not None:
        query = query.where(Task.project_id == project_id)
    if tag is not None:
        query = query.join(TaskTag, TaskTag.task_id == Task.id).where(TaskTag.tag == tag)

    if status_filter is not None:
        query = query.where(Task.status == status_filter.value)

    if assignee_id is not None:
        query = query.where(Task.assignee_id == assignee_id)

    if due_at_from is not None:
        query = query.where(Task.due_at >= due_at_from)

    if due_at_to is not None:
        query = query.where(Task.due_at <= due_at_to)

    return query


async def create_task(
    db: AsyncSession,
    *,
    workspace_id: int,
    project_id: int,
    actor_user_id: int,
    data: TaskCreate,
    idempotency_key: str | None,
    route: str,
) -> TaskResponse:
    await require_workspace_membership(db, workspace_id, actor_user_id)

    project_result = await db.execute(
        select(Project).where(
            Project.workspace_id == workspace_id,
            Project.id == project_id,
        )
    )
    if project_result.scalar_one_or_none() is None:
        raise NotFoundError("Project not found")

    if data.assignee_id is not None:
        await ensure_user_in_workspace(db, workspace_id, data.assignee_id)

    existing_record = None
    request_hash = None
    if idempotency_key:
        payload = data.model_dump(mode="json")
        request_hash = build_request_hash(payload)
        replay_payload, existing_record = await get_replay_response(
            db,
            user_id=actor_user_id,
            route=route,
            key=idempotency_key,
            request_hash=request_hash,
        )
        if replay_payload is not None:
            return TaskResponse.model_validate(replay_payload)

    task = Task(
        workspace_id=workspace_id,
        project_id=project_id,
        title=data.title,
        description=data.description,
        status=TaskStatus.todo.value,
        creator_id=actor_user_id,
        assignee_id=data.assignee_id,
        due_at=data.due_at,
        version=1,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)

    response_payload = TaskResponse.model_validate(task).model_dump(mode="json")

    if idempotency_key and request_hash is not None:
        await save_response(
            db,
            existing_record=existing_record,
            user_id=actor_user_id,
            route=route,
            key=idempotency_key,
            request_hash=request_hash,
            response_status=status.HTTP_201_CREATED,
            response_body=response_payload,
            resource_type="task",
            resource_id=task.id,
        )

    await log_action(
        db,
        actor_user_id=actor_user_id,
        workspace_id=workspace_id,
        entity_type="task",
        entity_id=task.id,
        action="create",
        changes={
            "project_id": project_id,
            "title": data.title,
            "assignee_id": data.assignee_id,
            "due_at": data.due_at,
        },
    )

    await db.commit()
    return TaskResponse.model_validate(task)


async def list_tasks(
    db: AsyncSession,
    *,
    workspace_id: int,
    user_id: int,
    skip: int,
    limit: int,
    sort_by: TaskSortBy,
    sort_order: SortOrder,
    status_filter: TaskStatus | None,
    assignee_id: int | None,
    project_id: int | None,
    tag: str | None,
    due_at_from: datetime | None,
    due_at_to: datetime | None,
) -> tuple[list[Task], int]:
    await require_workspace_membership(db, workspace_id, user_id)

    if due_at_from and due_at_to and due_at_from > due_at_to:
        raise BadRequestError("due_at_from cannot be greater than due_at_to")

    filter_kwargs = dict(
        status_filter=status_filter,
        assignee_id=assignee_id,
        project_id=project_id,
        tag=tag,
        due_at_from=due_at_from,
        due_at_to=due_at_to,
    )

    base_query = select(Task).where(Task.workspace_id == workspace_id)
    base_count = select(func.count(Task.id)).where(Task.workspace_id == workspace_id)

    query = _apply_task_filters(base_query, **filter_kwargs)
    count_query = _apply_task_filters(base_count, **filter_kwargs)

    sort_column = SORT_COLUMNS[sort_by]
    if sort_order == SortOrder.asc:
        query = query.order_by(sort_column.asc(), Task.id.asc())
    else:
        query = query.order_by(sort_column.desc(), Task.id.desc())

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    count_result = await db.execute(count_query)

    return list(result.scalars().all()), int(count_result.scalar_one())


async def get_task(
    db: AsyncSession,
    *,
    workspace_id: int,
    task_id: int,
    user_id: int,
) -> Task:
    await require_workspace_membership(db, workspace_id, user_id)

    task = await _get_task_scoped(db, workspace_id=workspace_id, task_id=task_id)
    if task is None:
        raise NotFoundError("Task not found")
    return task


async def update_task(
    db: AsyncSession,
    *,
    workspace_id: int,
    task_id: int,
    actor_user_id: int,
    data: TaskUpdate,
) -> Task:
    membership = await require_workspace_membership(db, workspace_id, actor_user_id)

    task = await _get_task_scoped(db, workspace_id=workspace_id, task_id=task_id)
    if task is None:
        raise NotFoundError("Task not found")

    if not _can_manage_task(task, membership.role, actor_user_id):
        raise ForbiddenError("Insufficient permissions")

    if data.version != task.version:
        raise ConflictError("Task version conflict")

    update_data = data.model_dump(exclude_unset=True, exclude={"version"})

    if "assignee_id" in update_data and update_data["assignee_id"] is not None:
        await ensure_user_in_workspace(db, workspace_id, update_data["assignee_id"])

    for field, value in update_data.items():
        setattr(task, field, value)

    if update_data:
        previous_version = task.version
        task.version += 1

        await log_action(
            db,
            actor_user_id=actor_user_id,
            workspace_id=workspace_id,
            entity_type="task",
            entity_id=task_id,
            action="update",
            changes={
                "changes": update_data,
                "version_from": previous_version,
                "version_to": task.version,
            },
        )

        await db.commit()
        await db.refresh(task)

    return task


async def transition_task_status(
    db: AsyncSession,
    *,
    workspace_id: int,
    task_id: int,
    actor_user_id: int,
    data: TaskStatusTransition,
) -> Task:
    membership = await require_workspace_membership(db, workspace_id, actor_user_id)

    task = await _get_task_scoped(db, workspace_id=workspace_id, task_id=task_id)
    if task is None:
        raise NotFoundError("Task not found")

    if not _can_manage_task(task, membership.role, actor_user_id):
        raise ForbiddenError("Insufficient permissions")

    from_status = TaskStatus(task.status)
    allowed = ALLOWED_TRANSITIONS[from_status]
    if data.to_status not in allowed:
        raise BadRequestError(
            f"Invalid status transition: {task.status} -> {data.to_status.value}"
        )

    previous_status = task.status
    previous_version = task.version
    task.status = data.to_status.value
    task.version += 1

    await log_action(
        db,
        actor_user_id=actor_user_id,
        workspace_id=workspace_id,
        entity_type="task",
        entity_id=task_id,
        action="status_transition",
        changes={
            "from": previous_status,
            "to": data.to_status.value,
            "version_from": previous_version,
            "version_to": task.version,
        },
    )

    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(
    db: AsyncSession,
    *,
    workspace_id: int,
    task_id: int,
    actor_user_id: int,
) -> None:
    membership = await require_workspace_membership(db, workspace_id, actor_user_id)

    task = await _get_task_scoped(db, workspace_id=workspace_id, task_id=task_id)
    if task is None:
        raise NotFoundError("Task not found")

    if not _can_manage_task(task, membership.role, actor_user_id):
        raise ForbiddenError("Insufficient permissions")

    await log_action(
        db,
        actor_user_id=actor_user_id,
        workspace_id=workspace_id,
        entity_type="task",
        entity_id=task_id,
        action="delete",
        changes={"title": task.title},
    )

    await db.delete(task)
    await db.commit()
