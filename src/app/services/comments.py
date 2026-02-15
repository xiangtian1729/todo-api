from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ForbiddenError, NotFoundError
from app.models.task import Task
from app.models.task_comment import TaskComment
from app.schemas.comment import CommentCreate, CommentUpdate
from app.services.audit import log_action
from app.services.permissions import ADMIN_ROLES, require_workspace_membership


async def _get_task(
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


async def create_comment(
    db: AsyncSession,
    *,
    workspace_id: int,
    task_id: int,
    actor_user_id: int,
    data: CommentCreate,
) -> TaskComment:
    await require_workspace_membership(db, workspace_id, actor_user_id)
    await _get_task(db, workspace_id=workspace_id, task_id=task_id)

    comment = TaskComment(
        workspace_id=workspace_id,
        task_id=task_id,
        author_id=actor_user_id,
        content=data.content,
    )
    db.add(comment)
    await db.flush()

    await log_action(
        db,
        actor_user_id=actor_user_id,
        workspace_id=workspace_id,
        entity_type="task_comment",
        entity_id=comment.id,
        action="create",
        changes={"task_id": task_id},
    )

    await db.commit()
    await db.refresh(comment)
    return comment


async def list_comments(
    db: AsyncSession,
    *,
    workspace_id: int,
    task_id: int,
    user_id: int,
) -> list[TaskComment]:
    await require_workspace_membership(db, workspace_id, user_id)
    await _get_task(db, workspace_id=workspace_id, task_id=task_id)

    result = await db.execute(
        select(TaskComment)
        .where(
            TaskComment.workspace_id == workspace_id,
            TaskComment.task_id == task_id,
        )
        .order_by(TaskComment.created_at.asc(), TaskComment.id.asc())
    )
    return list(result.scalars().all())


async def update_comment(
    db: AsyncSession,
    *,
    workspace_id: int,
    task_id: int,
    comment_id: int,
    actor_user_id: int,
    data: CommentUpdate,
) -> TaskComment:
    await require_workspace_membership(db, workspace_id, actor_user_id)
    await _get_task(db, workspace_id=workspace_id, task_id=task_id)

    result = await db.execute(
        select(TaskComment).where(
            TaskComment.workspace_id == workspace_id,
            TaskComment.task_id == task_id,
            TaskComment.id == comment_id,
        )
    )
    comment = result.scalar_one_or_none()
    if comment is None:
        raise NotFoundError("Comment not found")

    if comment.author_id != actor_user_id:
        raise ForbiddenError("Only the comment author can edit this comment")

    previous_content = comment.content
    comment.content = data.content

    await log_action(
        db,
        actor_user_id=actor_user_id,
        workspace_id=workspace_id,
        entity_type="task_comment",
        entity_id=comment_id,
        action="update",
        changes={"from": previous_content, "to": data.content},
    )

    await db.commit()
    await db.refresh(comment)
    return comment


async def delete_comment(
    db: AsyncSession,
    *,
    workspace_id: int,
    task_id: int,
    comment_id: int,
    actor_user_id: int,
) -> None:
    membership = await require_workspace_membership(db, workspace_id, actor_user_id)
    await _get_task(db, workspace_id=workspace_id, task_id=task_id)

    result = await db.execute(
        select(TaskComment).where(
            TaskComment.workspace_id == workspace_id,
            TaskComment.task_id == task_id,
            TaskComment.id == comment_id,
        )
    )
    comment = result.scalar_one_or_none()
    if comment is None:
        raise NotFoundError("Comment not found")

    if comment.author_id != actor_user_id and membership.role not in ADMIN_ROLES:
        raise ForbiddenError("Insufficient permissions")

    await log_action(
        db,
        actor_user_id=actor_user_id,
        workspace_id=workspace_id,
        entity_type="task_comment",
        entity_id=comment_id,
        action="delete",
        changes={"author_id": comment.author_id},
    )

    await db.delete(comment)
    await db.commit()
