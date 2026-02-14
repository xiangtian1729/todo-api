"""
测试配置文件（conftest.py）

提供共享的测试工具（fixture）：
1. 独立的内存测试数据库
2. HTTP 测试客户端
3. 已登录的客户端（自动带 JWT token）
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db
from app.main import app
from app.models.todo import Base

# 测试用内存数据库
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_database():
    """每个测试前创建表，测试后销毁"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    async with test_session() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def client():
    """未认证的 HTTP 客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_client(client: AsyncClient):
    """已认证的 HTTP 客户端（自动注册、登录、带 token）

    这个 fixture 帮你省去每个测试里都要注册+登录的重复步骤。
    """
    # 注册测试用户
    await client.post("/auth/register", json={
        "username": "testuser",
        "password": "testpass123",
    })
    # 登录获取 token
    login_resp = await client.post("/auth/login", data={
        "username": "testuser",
        "password": "testpass123",
    })
    token = login_resp.json()["access_token"]

    # 设置请求头，之后所有请求都自动带 token
    client.headers["Authorization"] = f"Bearer {token}"
    yield client
