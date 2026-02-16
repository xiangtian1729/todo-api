from datetime import datetime

from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.task import (
    SortOrder,
    TaskCreate,
    TaskResponse,
    TaskSortBy,
    TaskStatus,
    TaskStatusTransition,
    TaskUpdate,
)
from app.security import get_current_user
from app.services import tasks as task_service

router = APIRouter(tags=["Tasks"])


@router.post(
    "/workspaces/{workspace_id}/projects/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    request: Request,
    workspace_id: int,
    project_id: int,
    data: TaskCreate,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    return await task_service.create_task(
        db,
        workspace_id=workspace_id,
        project_id=project_id,
        actor_user_id=current_user.id,
        data=data,
        idempotency_key=idempotency_key,
        route=request.url.path,
    )


@router.get(
    "/workspaces/{workspace_id}/tasks",
    response_model=PageResponse[TaskResponse],
)
async def list_tasks(
    workspace_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    sort_by: TaskSortBy = Query(default=TaskSortBy.created_at),
    sort_order: SortOrder = Query(default=SortOrder.desc),
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    assignee_id: int | None = Query(default=None, ge=1),
    project_id: int | None = Query(default=None, ge=1),
    tag: str | None = Query(default=None, min_length=1, max_length=50),
    due_at_from: datetime | None = None,
    due_at_to: datetime | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    items, total = await task_service.list_tasks(
        db,
        workspace_id=workspace_id,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        status_filter=status_filter,
        assignee_id=assignee_id,
        project_id=project_id,
        tag=tag,
        due_at_from=due_at_from,
        due_at_to=due_at_to,
    )
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get(
    "/workspaces/{workspace_id}/tasks/{task_id}",
    response_model=TaskResponse,
)
async def get_task(
    workspace_id: int,
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    return await task_service.get_task(
        db,
        workspace_id=workspace_id,
        task_id=task_id,
        user_id=current_user.id,
    )


@router.patch(
    "/workspaces/{workspace_id}/tasks/{task_id}",
    response_model=TaskResponse,
)
async def update_task(
    workspace_id: int,
    task_id: int,
    data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    return await task_service.update_task(
        db,
        workspace_id=workspace_id,
        task_id=task_id,
        actor_user_id=current_user.id,
        data=data,
    )


@router.post(
    "/workspaces/{workspace_id}/tasks/{task_id}/status-transitions",
    response_model=TaskResponse,
)
async def transition_task_status(
    workspace_id: int,
    task_id: int,
    data: TaskStatusTransition,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    return await task_service.transition_task_status(
        db,
        workspace_id=workspace_id,
        task_id=task_id,
        actor_user_id=current_user.id,
        data=data,
    )


@router.delete(
    "/workspaces/{workspace_id}/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_task(
    workspace_id: int,
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await task_service.delete_task(
        db,
        workspace_id=workspace_id,
        task_id=task_id,
        actor_user_id=current_user.id,
    )
