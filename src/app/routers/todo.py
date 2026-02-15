"""
Todo API 路由模块

所有端点都需要登录后才能访问（通过 JWT token）。
每个用户只能看到和操作自己的 Todo。
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.todo import Todo
from app.models.user import User
from app.schemas.todo import TodoCreate, TodoResponse, TodoUpdate
from app.security import get_current_user

router = APIRouter(prefix="/todos", tags=["Todos"])


# ========== POST /todos — 创建新的 Todo ==========
@router.post(
    "/",
    response_model=TodoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建待办事项",
)
async def create_todo(
    todo_in: TodoCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Todo:
    """创建 Todo 并关联到当前登录用户"""
    todo = Todo(**todo_in.model_dump(), user_id=current_user.id)
    db.add(todo)
    await db.commit()
    await db.refresh(todo)
    return todo


# ========== GET /todos — 获取当前用户的 Todo 列表 ==========
@router.get(
    "/",
    response_model=list[TodoResponse],
    summary="获取待办事项列表",
)
async def list_todos(
    skip: int = Query(default=0, ge=0, description="跳过的记录数（>= 0）"),
    limit: int = Query(default=20, ge=1, le=100, description="每页数量（1-100）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Todo]:
    """只返回当前用户的 Todo"""
    query = (
        select(Todo)
        .where(Todo.user_id == current_user.id)
        .order_by(Todo.created_at.desc(), Todo.id.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


# ========== GET /todos/{todo_id} — 获取单个 Todo ==========
@router.get(
    "/{todo_id}",
    response_model=TodoResponse,
    summary="获取单个待办事项",
)
async def get_todo(
    todo_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Todo:
    """获取指定 Todo（必须属于当前用户）"""
    todo = await db.get(Todo, todo_id)

    if todo is None or todo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found",
        )
    return todo


# ========== PATCH /todos/{todo_id} — 更新 Todo ==========
@router.patch(
    "/{todo_id}",
    response_model=TodoResponse,
    summary="更新待办事项",
)
async def update_todo(
    todo_id: int,
    todo_in: TodoUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Todo:
    """更新指定 Todo（必须属于当前用户）"""
    todo = await db.get(Todo, todo_id)

    if todo is None or todo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found",
        )

    update_data = todo_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(todo, field, value)

    await db.commit()
    await db.refresh(todo)
    return todo


# ========== DELETE /todos/{todo_id} — 删除 Todo ==========
@router.delete(
    "/{todo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除待办事项",
)
async def delete_todo(
    todo_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """删除指定 Todo（必须属于当前用户）"""
    todo = await db.get(Todo, todo_id)

    if todo is None or todo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found",
        )

    await db.delete(todo)
    await db.commit()
