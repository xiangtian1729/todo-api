"""
认证相关测试

测试用户注册和登录功能。
"""

from httpx import AsyncClient


class TestRegister:

    async def test_register_success(self, client: AsyncClient):
        """正常注册"""
        response = await client.post("/auth/register", json={
            "username": "alice",
            "password": "secret123",
        })

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "alice"
        assert "password" not in data         # 响应中不能包含密码
        assert "hashed_password" not in data  # 也不能包含哈希密码

    async def test_register_duplicate_username(self, client: AsyncClient):
        """重复用户名应该失败"""
        await client.post("/auth/register", json={
            "username": "bob",
            "password": "secret123",
        })
        # 再次注册相同用户名
        response = await client.post("/auth/register", json={
            "username": "bob",
            "password": "different",
        })

        assert response.status_code == 409

    async def test_register_short_password(self, client: AsyncClient):
        """密码太短应该失败（最少 6 位）"""
        response = await client.post("/auth/register", json={
            "username": "charlie",
            "password": "123",
        })
        assert response.status_code == 422


class TestLogin:

    async def test_login_success(self, client: AsyncClient):
        """正常登录，获取 token"""
        # 先注册
        await client.post("/auth/register", json={
            "username": "alice",
            "password": "secret123",
        })
        # 登录（OAuth2 表单格式用 data= 而不是 json=）
        response = await client.post("/auth/login", data={
            "username": "alice",
            "password": "secret123",
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient):
        """密码错误应该返回 401"""
        await client.post("/auth/register", json={
            "username": "alice",
            "password": "secret123",
        })
        response = await client.post("/auth/login", data={
            "username": "alice",
            "password": "wrongpass",
        })

        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """不存在的用户应该返回 401"""
        response = await client.post("/auth/login", data={
            "username": "ghost",
            "password": "secret123",
        })
        assert response.status_code == 401
