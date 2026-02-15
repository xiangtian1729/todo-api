import asyncio
import os
import subprocess
import sys
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db
from app.main import app

ROOT_DIR = Path(__file__).resolve().parents[1]
TEST_DB_PATH = ROOT_DIR / "tests" / "test_api.db"
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH.as_posix()}"
TEST_SCHEMA_REVISION = "head"

TABLES_TO_CLEAN = [
    "task_watchers",
    "task_tags",
    "task_comments",
    "audit_logs",
    "idempotency_keys",
    "tasks",
    "workspace_memberships",
    "projects",
    "workspaces",
    "users",
]


def _run_alembic(*args: str) -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = TEST_DATABASE_URL
    subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=ROOT_DIR,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def migrated_schema() -> None:
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    _run_alembic("upgrade", TEST_SCHEMA_REVISION)
    yield

    asyncio.run(test_engine.dispose())
    _run_alembic("downgrade", "base")
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture(autouse=True)
async def cleanup_database(migrated_schema):
    async with test_engine.begin() as conn:
        await conn.execute(text("PRAGMA foreign_keys=OFF"))
        for table in TABLES_TO_CLEAN:
            await conn.execute(text(f"DELETE FROM {table}"))

        seq_exists = await conn.execute(
            text(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='sqlite_sequence'"
            )
        )
        if seq_exists.scalar_one_or_none() is not None:
            await conn.execute(text("DELETE FROM sqlite_sequence"))

        await conn.execute(text("PRAGMA foreign_keys=ON"))
    yield


async def override_get_db():
    async with test_session() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_client(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={"username": "testuser", "password": "testpass123"},
    )
    login_resp = await client.post(
        "/auth/login",
        data={"username": "testuser", "password": "testpass123"},
    )
    token = login_resp.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    yield client
