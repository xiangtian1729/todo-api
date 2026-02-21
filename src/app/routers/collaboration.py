from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.comment import (
    CommentCreate,
    CommentResponse,
    CommentUpdate,
    TagCreate,
    TagResponse,
    WatcherCreate,
    WatcherResponse,
)
from app.security import get_current_user
from app.services import comments as comment_service
from app.services import tags as tag_service
from app.services import watchers as watcher_service

router = APIRouter(tags=["Collaboration"])


@router.post(
    "/workspaces/{workspace_id}/tasks/{task_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    workspace_id: int,
    task_id: int,
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommentResponse:
    comment = await comment_service.create_comment(
        db,
        workspace_id=workspace_id,
        task_id=task_id,
        actor_user_id=current_user.id,
        data=data,
    )
    return CommentResponse.model_validate(comment)


@router.get(
    "/workspaces/{workspace_id}/tasks/{task_id}/comments",
    response_model=list[CommentResponse],
)
async def list_comments(
    workspace_id: int,
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CommentResponse]:
    comments = await comment_service.list_comments(
        db,
        workspace_id=workspace_id,
        task_id=task_id,
        user_id=current_user.id,
    )
    return [CommentResponse.model_validate(comment) for comment in comments]


@router.patch(
    "/workspaces/{workspace_id}/tasks/{task_id}/comments/{comment_id}",
    response_model=CommentResponse,
)
async def update_comment(
    workspace_id: int,
    task_id: int,
    comment_id: int,
    data: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommentResponse:
    comment = await comment_service.update_comment(
        db,
        workspace_id=workspace_id,
        task_id=task_id,
        comment_id=comment_id,
        actor_user_id=current_user.id,
        data=data,
    )
    return CommentResponse.model_validate(comment)


@router.delete(
    "/workspaces/{workspace_id}/tasks/{task_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_comment(
    workspace_id: int,
    task_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await comment_service.delete_comment(
        db,
        workspace_id=workspace_id,
        task_id=task_id,
        comment_id=comment_id,
        actor_user_id=current_user.id,
    )


@router.get(
    "/workspaces/{workspace_id}/tasks/{task_id}/tags",
    response_model=list[TagResponse],
)
async def list_tags(
    workspace_id: int,
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TagResponse]:
    tags = await tag_service.list_tags(
        db,
        workspace_id=workspace_id,
        task_id=task_id,
        actor_user_id=current_user.id,
    )
    return [TagResponse.model_validate(t) for t in tags]


@router.post(
    "/workspaces/{workspace_id}/tasks/{task_id}/tags",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_tag(
    workspace_id: int,
    task_id: int,
    data: TagCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TagResponse:
    tag = await tag_service.add_tag(
        db,
        workspace_id=workspace_id,
        task_id=task_id,
        actor_user_id=current_user.id,
        data=data,
    )
    return TagResponse.model_validate(tag)


@router.delete(
    "/workspaces/{workspace_id}/tasks/{task_id}/tags/{tag}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_tag(
    workspace_id: int,
    task_id: int,
    tag: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await tag_service.delete_tag(
        db,
        workspace_id=workspace_id,
        task_id=task_id,
        tag_value=tag,
        actor_user_id=current_user.id,
    )


@router.get(
    "/workspaces/{workspace_id}/tasks/{task_id}/watchers",
    response_model=list[WatcherResponse],
)
async def list_watchers(
    workspace_id: int,
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[WatcherResponse]:
    watchers = await watcher_service.list_watchers(
        db,
        workspace_id=workspace_id,
        task_id=task_id,
        actor_user_id=current_user.id,
    )
    return [WatcherResponse.model_validate(w) for w in watchers]


@router.post(
    "/workspaces/{workspace_id}/tasks/{task_id}/watchers",
    response_model=WatcherResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_watcher(
    workspace_id: int,
    task_id: int,
    data: WatcherCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WatcherResponse:
    watcher = await watcher_service.add_watcher(
        db,
        workspace_id=workspace_id,
        task_id=task_id,
        actor_user_id=current_user.id,
        data=data,
    )
    return WatcherResponse.model_validate(watcher)


@router.delete(
    "/workspaces/{workspace_id}/tasks/{task_id}/watchers/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_watcher(
    workspace_id: int,
    task_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await watcher_service.delete_watcher(
        db,
        workspace_id=workspace_id,
        task_id=task_id,
        watcher_user_id=user_id,
        actor_user_id=current_user.id,
    )
