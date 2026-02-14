"""
Todo 数据验证模型（Schemas）

为什么 models/ 和 schemas/ 要分开？

    models/ 里的模型 = 数据库表的结构（给数据库看的）
    schemas/ 里的模型 = API 请求/响应的数据格式（给用户看的）

    它们虽然很像，但职责不同：
    - 用户创建 Todo 时，不需要传 id、created_at（这些是自动生成的）
    - 返回 Todo 给用户时，要包含 id、created_at 等所有信息
    - 更新 Todo 时，所有字段都应该是可选的（用户可能只想改标题）

    所以我们需要不同的 Schema 来处理不同的场景。

Pydantic 是 FastAPI 的核心组件之一，它能：
    1. 自动验证数据类型（传了字符串但期望整数？自动报错）
    2. 自动转换数据类型（传了 "true" 字符串？自动转成布尔值 True）
    3. 自动生成 API 文档中的请求/响应格式说明
"""

from datetime import datetime

from pydantic import BaseModel, Field


# ========== 创建 Todo 的请求格式 ==========
class TodoCreate(BaseModel):
    """创建新 Todo 时，用户需要提供的数据

    用户只需要提供 title（必填）和 description（可选）。
    其他字段（id, is_completed, created_at 等）由系统自动处理。
    """

    title: str = Field(
        ...,                    # ... 表示这是必填字段
        min_length=1,           # 最少 1 个字符（不能为空标题）
        max_length=200,         # 最多 200 个字符（与数据库定义一致）
        examples=["买菜"],      # API 文档中的示例值
        description="待办事项的标题",
    )
    description: str | None = Field(
        default=None,           # 默认为空，可选字段
        max_length=2000,        # 描述最多 2000 字符
        examples=["去超市买今晚做饭需要的蔬菜和肉"],
        description="待办事项的详细描述（可选）",
    )


# ========== 更新 Todo 的请求格式 ==========
class TodoUpdate(BaseModel):
    """更新 Todo 时，用户可以提供的数据

    所有字段都是可选的——用户可能只想改标题，或者只想标记为完成。
    只有用户传了的字段才会被更新，其他字段保持不变。
    """

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="新的标题",
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="新的描述",
    )
    is_completed: bool | None = Field(
        default=None,
        description="是否已完成",
    )


# ========== 返回给用户的 Todo 格式 ==========
class TodoResponse(BaseModel):
    """返回给用户的完整 Todo 数据

    包含所有字段，包括系统自动生成的 id 和时间戳。

    model_config 中的 from_attributes = True 让 Pydantic 能直接
    从 SQLAlchemy 的模型对象中读取数据，无需手动转换。
    （相当于告诉 Pydantic："你可以从 ORM 对象的属性里取值"）
    """

    id: int
    title: str
    description: str | None
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
