"""
数据库连接与会话管理模块

为什么需要这个文件？
    这个文件负责：
    1. 创建数据库"引擎"（Engine）—— 好比打开了数据库的大门
    2. 创建"会话工厂"（Session）—— 好比拿到了一张工作台
    3. 提供一个获取数据库会话的函数 —— 每次 API 请求来了，分配一张工作台

关键概念：
    - Engine（引擎）：管理与数据库的底层连接
    - Session（会话）：在这张"工作台"上执行数据库操作（增删改查）
    - 每次操作完成后要"归还"工作台（关闭会话），避免资源泄漏
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# ========== 第一步：创建数据库引擎 ==========
# engine 就像一个"连接池管理员"，负责管理与数据库的连接
# echo=True 表示在控制台打印所有 SQL 语句（方便调试学习，生产环境应关闭）
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # 开发时打印 SQL，方便我们学习 ORM 在背后做了什么
)

# ========== 第二步：创建会话工厂 ==========
# async_sessionmaker 是一个"会话制造机"
# 每次调用它，就会生产一个新的数据库会话（工作台）
# expire_on_commit=False：提交后不自动过期对象，避免访问已提交数据时出错
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ========== 第三步：定义获取会话的依赖函数 ==========
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的依赖注入函数

    这是 FastAPI 的"依赖注入"模式：
    - FastAPI 在处理每个请求时，会自动调用这个函数
    - 函数使用 yield（而不是 return）返回会话
    - yield 之前的代码在请求开始时执行（打开会话）
    - yield 之后的代码在请求结束时执行（关闭会话）

    这保证了每个请求都有独立的会话，且请求结束后一定会被关闭，
    不会因为忘记关闭而导致数据库连接泄漏。

    好比：
        开门 → 给你一张工作台 → 你干活 → 干完了我帮你收拾并关门
    """
    async with async_session() as session:
        yield session
