"""
用户数据库模型

定义 users 表的结构：
    users(id, username, hashed_password, created_at)
    主键：id
    唯一约束：username
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.todo import Base


class User(Base):
    """用户模型

    属性说明：
        id:              主键，自增长
        username:        用户名，唯一，用于登录
        hashed_password: 哈希后的密码（永远不存储明文密码！）
        created_at:      注册时间
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True,
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,        # 用户名不能重复
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
