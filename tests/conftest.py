"""
测试配置文件（conftest.py）

这个文件为所有测试提供共享的"测试工具"（fixture）：
1. 一个独立的测试数据库（不影响开发数据）
2. 一个数据库会话（用于测试中操作数据库）
3. 一个 HTTP 客户端（用于模拟发送 API 请求）

为什么测试需要单独的数据库？
    如果测试和开发共用同一个数据库，测试时创建/删除的数据
    会搞乱你开发中的数据。测试数据库用完就扔，互不干扰。
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db
from app.main import app
from app.models.todo import Base

# 测试用的独立数据库（使用 SQLite 内存数据库，速度快，用完自动消失）
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# 创建测试专用的引擎和会话工厂
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_database():
    """每个测试函数运行前，自动创建全新的数据库表；运行后自动销毁。

    autouse=True 表示所有测试函数都会自动使用这个 fixture，无需手动声明。
    这保证了每个测试都在"干净"的数据库上运行，互不影响。
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)   # 创建表
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)      # 销毁表


async def override_get_db():
    """替换掉 app 中的 get_db，让 API 使用测试数据库而不是开发数据库。"""
    async with test_session() as session:
        yield session


# 关键：告诉 FastAPI "在测试中，用 override_get_db 替代 get_db"
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def client():
    """创建一个异步 HTTP 测试客户端。

    这个客户端可以向我们的 FastAPI 应用发送请求（GET, POST, PATCH, DELETE），
    但不需要真正启动服务器——它在内存中直接调用应用。
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
