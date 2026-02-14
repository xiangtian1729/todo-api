"""
Todo 数据库模型

这个文件定义了 "todos" 表在数据库里长什么样。
还记得 ORM 是"翻译官"吗？这里就是告诉翻译官：
    "我要一张叫 todos 的表，里面有这些列……"

SQLAlchemy 会自动根据这个类，在数据库里创建出对应的表。

对应的数据库表结构（您学过的关系模型）：
    todos(id, title, description, is_completed, created_at, updated_at)
    主键：id
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有数据库模型的基类

    SQLAlchemy 要求所有的模型类都继承自同一个 Base 类。
    这个 Base 类会自动收集所有继承它的模型，
    后续创建数据库表时，只需要告诉 SQLAlchemy："把 Base 认识的所有表都建出来"。
    """

    pass


class Todo(Base):
    """Todo 待办事项模型

    每一个 Todo 实例对应数据库 todos 表中的一行记录。

    属性说明：
        id:             主键，自增长整数，由数据库自动生成
        title:          标题，必填，最长 200 字符
        description:    详细描述，可选，使用 Text 类型支持长文本
        is_completed:   是否完成，默认 False
        created_at:     创建时间，由数据库自动记录
        updated_at:     最后更新时间，每次修改时自动更新
    """

    # __tablename__ 指定这个模型对应数据库里的哪张表
    __tablename__ = "todos"

    # ========== 列定义 ==========
    # Mapped[int] 是类型提示，告诉 Python 和 IDE 这个属性是 int 类型
    # mapped_column(...) 定义这个列在数据库中的具体属性

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,   # 主键
        autoincrement=True, # 自增长：1, 2, 3, ...
    )

    title: Mapped[str] = mapped_column(
        String(200),        # 最长 200 个字符的字符串
        nullable=False,     # 不允许为空（NOT NULL）
    )

    description: Mapped[str | None] = mapped_column(
        Text,               # 长文本类型，不限长度
        nullable=True,      # 允许为空（可选字段）
        default=None,
    )

    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,      # 默认未完成
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # 由数据库服务器自动填入当前时间
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),  # 每次更新记录时，自动刷新为当前时间
        nullable=False,
    )

    def __repr__(self) -> str:
        """定义打印 Todo 对象时的显示格式，方便调试

        例如：<Todo(id=1, title='买菜', is_completed=False)>
        """
        return f"<Todo(id={self.id}, title='{self.title}', is_completed={self.is_completed})>"
