"""
Todo API 路由模块

这个文件定义了所有与 Todo 相关的 API 端点（Endpoint）。
每个端点就是一个 URL + HTTP 方法的组合，对应一个操作。

我们实现标准的 RESTful CRUD 操作：
    C - Create（创建）  → POST   /todos
    R - Read（读取）    → GET    /todos      （获取列表）
                        → GET    /todos/{id}  （获取单个）
    U - Update（更新）  → PATCH  /todos/{id}
    D - Delete（删除）  → DELETE /todos/{id}

为什么用 PATCH 而不是 PUT？
    - PUT：需要发送完整的对象来替换（你必须发送所有字段）
    - PATCH：只发送需要修改的字段（更灵活，更常用）

HTTP 状态码约定：
    200 OK          → 操作成功（返回数据）
    201 Created     → 创建成功
    204 No Content  → 删除成功（不返回数据）
    404 Not Found   → 找不到指定的资源
    422 Unprocessable Entity → 客户端发送的数据格式不正确
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoResponse, TodoUpdate

# ========== 创建路由器 ==========
# APIRouter 相当于一个"子应用"，把相关的端点组织在一起
# prefix="/todos" 表示这个路由器下所有端点都以 /todos 开头
# tags=["Todos"] 用于在 API 文档中归类
router = APIRouter(prefix="/todos", tags=["Todos"])


# ========== POST /todos —— 创建新的 Todo ==========
@router.post(
    "/",
    response_model=TodoResponse,    # 指定返回数据的格式
    status_code=status.HTTP_201_CREATED,  # 创建成功返回 201
    summary="创建待办事项",
    description="创建一个新的待办事项，需要提供标题，描述可选。",
)
async def create_todo(
    todo_in: TodoCreate,                          # FastAPI 自动从请求体解析并验证
    db: AsyncSession = Depends(get_db),            # 依赖注入：自动获取数据库会话
) -> Todo:
    """
    执行流程：
    1. FastAPI 自动把用户发的 JSON 解析为 TodoCreate 对象（并验证格式）
    2. 用 TodoCreate 的数据创建一个 Todo 数据库模型实例
    3. 添加到数据库会话 → 提交 → 刷新（获取数据库生成的 id 和时间戳）
    4. 返回新创建的 Todo（FastAPI 自动按 TodoResponse 格式返回 JSON）
    """
    # 把用户输入的数据转换为数据库模型
    # **todo_in.model_dump() 是 Python 的"解包"语法，相当于：
    # Todo(title=todo_in.title, description=todo_in.description)
    todo = Todo(**todo_in.model_dump())

    db.add(todo)           # 告诉数据库会话："我要添加这条记录"
    await db.commit()      # 提交事务：真正写入数据库
    await db.refresh(todo) # 刷新：从数据库读回最新数据（包括自动生成的 id、时间戳）

    return todo


# ========== GET /todos —— 获取 Todo 列表 ==========
@router.get(
    "/",
    response_model=list[TodoResponse],  # 返回 TodoResponse 的列表
    summary="获取待办事项列表",
    description="获取所有待办事项的列表，支持分页。",
)
async def list_todos(
    skip: int = 0,                          # 跳过前 N 条（分页用）
    limit: int = 20,                        # 每页最多返回 N 条
    db: AsyncSession = Depends(get_db),
) -> list[Todo]:
    """
    分页参数示例：
        GET /todos             → 返回前 20 条
        GET /todos?skip=20     → 跳过前 20 条，返回第 21-40 条
        GET /todos?limit=5     → 只返回前 5 条

    select(Todo) 对应 SQL：SELECT * FROM todos
    .offset(skip) 对应 SQL：OFFSET skip
    .limit(limit) 对应 SQL：LIMIT limit
    """
    query = select(Todo).offset(skip).limit(limit)
    result = await db.execute(query)
    todos = result.scalars().all()  # scalars() 提取出 Todo 对象列表

    return todos


# ========== GET /todos/{todo_id} —— 获取单个 Todo ==========
@router.get(
    "/{todo_id}",
    response_model=TodoResponse,
    summary="获取单个待办事项",
    description="根据 ID 获取指定的待办事项。",
)
async def get_todo(
    todo_id: int,                           # 从 URL 路径中提取 todo_id
    db: AsyncSession = Depends(get_db),
) -> Todo:
    """
    示例：GET /todos/1 → 获取 id 为 1 的 Todo

    如果找不到，返回 404 错误。
    """
    todo = await db.get(Todo, todo_id)  # 按主键查找

    if todo is None:
        # 抛出 HTTP 异常，FastAPI 自动转换为 JSON 错误响应
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found",
        )

    return todo


# ========== PATCH /todos/{todo_id} —— 更新 Todo ==========
@router.patch(
    "/{todo_id}",
    response_model=TodoResponse,
    summary="更新待办事项",
    description="根据 ID 更新指定的待办事项，只需提供要修改的字段。",
)
async def update_todo(
    todo_id: int,
    todo_in: TodoUpdate,                    # 用户发送的更新数据
    db: AsyncSession = Depends(get_db),
) -> Todo:
    """
    示例：PATCH /todos/1 + {"is_completed": true}
    → 只修改 is_completed 字段，其他字段保持不变

    exclude_unset=True 的关键作用：
        只提取用户"实际发送"的字段，忽略未发送的字段（即使它们有默认值 None）。
        这样就不会把用户没发送的字段误更新为 None。
    """
    # 先查找要更新的 Todo
    todo = await db.get(Todo, todo_id)

    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found",
        )

    # 只更新用户发送的字段
    update_data = todo_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(todo, field, value)  # 动态设置属性值

    await db.commit()
    await db.refresh(todo)

    return todo


# ========== DELETE /todos/{todo_id} —— 删除 Todo ==========
@router.delete(
    "/{todo_id}",
    status_code=status.HTTP_204_NO_CONTENT,   # 删除成功不返回内容
    summary="删除待办事项",
    description="根据 ID 删除指定的待办事项。",
)
async def delete_todo(
    todo_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    示例：DELETE /todos/1 → 删除 id 为 1 的 Todo

    删除成功返回 204 No Content（无响应体）。
    如果找不到要删除的 Todo，返回 404 错误。
    """
    todo = await db.get(Todo, todo_id)

    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found",
        )

    await db.delete(todo)
    await db.commit()
