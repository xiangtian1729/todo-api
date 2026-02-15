"""
Todo API 端点测试

所有 Todo 操作现在需要登录（JWT token），
所以测试使用 auth_client fixture（自动带 token）。
"""

from httpx import AsyncClient


async def _get_auth_headers(
    client: AsyncClient,
    username: str,
    password: str = "secret123",
) -> dict[str, str]:
    register_resp = await client.post("/auth/register", json={
        "username": username,
        "password": password,
    })
    assert register_resp.status_code == 201

    login_resp = await client.post("/auth/login", data={
        "username": username,
        "password": password,
    })
    assert login_resp.status_code == 200

    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ========================================================================
# POST /todos/ — 创建 Todo 的测试
# ========================================================================

class TestCreateTodo:

    async def test_create_todo_success(self, auth_client: AsyncClient):
        """正常创建一个 Todo"""
        payload = {"title": "学习 Python", "description": "完成第一章"}

        response = await auth_client.post("/todos/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "学习 Python"
        assert data["description"] == "完成第一章"
        assert data["is_completed"] is False
        assert data["priority"] == 2

    async def test_create_todo_without_description(self, auth_client: AsyncClient):
        """创建时不写描述"""
        response = await auth_client.post("/todos/", json={"title": "买菜"})

        assert response.status_code == 201
        assert response.json()["description"] is None

    async def test_create_todo_empty_title_fails(self, auth_client: AsyncClient):
        """空标题应该失败"""
        response = await auth_client.post("/todos/", json={"title": ""})
        assert response.status_code == 422

    async def test_create_todo_missing_title_fails(self, auth_client: AsyncClient):
        """缺少标题应该失败"""
        response = await auth_client.post("/todos/", json={"description": "无标题"})
        assert response.status_code == 422

    async def test_create_todo_with_priority(self, auth_client: AsyncClient):
        """创建时指定优先级"""
        response = await auth_client.post("/todos/", json={"title": "紧急", "priority": 3})

        assert response.status_code == 201
        assert response.json()["priority"] == 3

    async def test_create_todo_invalid_priority_fails(self, auth_client: AsyncClient):
        """优先级超出范围应该失败"""
        response = await auth_client.post("/todos/", json={"title": "测试", "priority": 5})
        assert response.status_code == 422

    async def test_create_todo_without_auth_fails(self, client: AsyncClient):
        """不带 token 应该被拒绝"""
        response = await client.post("/todos/", json={"title": "测试"})
        assert response.status_code == 401


# ========================================================================
# GET /todos/ — 获取 Todo 列表
# ========================================================================

class TestListTodos:

    async def test_list_todos_empty(self, auth_client: AsyncClient):
        """空列表"""
        response = await auth_client.get("/todos/")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_todos_with_data(self, auth_client: AsyncClient):
        """有数据时返回列表"""
        await auth_client.post("/todos/", json={"title": "Todo 1"})
        await auth_client.post("/todos/", json={"title": "Todo 2"})

        response = await auth_client.get("/todos/")

        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_list_todos_with_pagination(self, auth_client: AsyncClient):
        """分页测试"""
        for i in range(3):
            await auth_client.post("/todos/", json={"title": f"Todo {i + 1}"})

        response = await auth_client.get("/todos/", params={"skip": 1, "limit": 1})

        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Todo 2"

    async def test_list_todos_negative_skip_fails(self, auth_client: AsyncClient):
        """skip < 0 时应返回 422"""
        response = await auth_client.get("/todos/", params={"skip": -1, "limit": 10})
        assert response.status_code == 422

    async def test_list_todos_limit_out_of_range_fails(self, auth_client: AsyncClient):
        """limit 超出范围时应返回 422"""
        response = await auth_client.get("/todos/", params={"skip": 0, "limit": 101})
        assert response.status_code == 422


# ========================================================================
# GET /todos/{id} — 获取单个 Todo
# ========================================================================

class TestGetTodo:

    async def test_get_todo_success(self, auth_client: AsyncClient):
        """正常获取"""
        create_resp = await auth_client.post("/todos/", json={"title": "测试"})
        todo_id = create_resp.json()["id"]

        response = await auth_client.get(f"/todos/{todo_id}")

        assert response.status_code == 200
        assert response.json()["title"] == "测试"

    async def test_get_todo_not_found(self, auth_client: AsyncClient):
        """找不到返回 404"""
        response = await auth_client.get("/todos/999")
        assert response.status_code == 404


# ========================================================================
# 用户隔离权限测试（A 不能操作 B 的 Todo）
# ========================================================================

class TestTodoAuthorizationIsolation:

    async def test_user_cannot_read_others_todo(self, client: AsyncClient):
        headers_a = await _get_auth_headers(client, "alice")
        create_resp = await client.post("/todos/", json={"title": "Alice Todo"}, headers=headers_a)
        todo_id = create_resp.json()["id"]

        headers_b = await _get_auth_headers(client, "bob")
        response = await client.get(f"/todos/{todo_id}", headers=headers_b)

        assert response.status_code == 404

    async def test_user_cannot_update_others_todo(self, client: AsyncClient):
        headers_a = await _get_auth_headers(client, "alice")
        create_resp = await client.post("/todos/", json={"title": "Alice Todo"}, headers=headers_a)
        todo_id = create_resp.json()["id"]

        headers_b = await _get_auth_headers(client, "bob")
        response = await client.patch(f"/todos/{todo_id}", json={"title": "Hacked"}, headers=headers_b)

        assert response.status_code == 404

    async def test_user_cannot_delete_others_todo(self, client: AsyncClient):
        headers_a = await _get_auth_headers(client, "alice")
        create_resp = await client.post("/todos/", json={"title": "Alice Todo"}, headers=headers_a)
        todo_id = create_resp.json()["id"]

        headers_b = await _get_auth_headers(client, "bob")
        response = await client.delete(f"/todos/{todo_id}", headers=headers_b)

        assert response.status_code == 404

    async def test_list_only_returns_current_user_todos(self, client: AsyncClient):
        headers_a = await _get_auth_headers(client, "alice")
        await client.post("/todos/", json={"title": "A1"}, headers=headers_a)
        await client.post("/todos/", json={"title": "A2"}, headers=headers_a)

        headers_b = await _get_auth_headers(client, "bob")
        await client.post("/todos/", json={"title": "B1"}, headers=headers_b)

        response = await client.get("/todos/", headers=headers_b)
        data = response.json()

        assert response.status_code == 200
        assert len(data) == 1
        assert data[0]["title"] == "B1"


# ========================================================================
# PATCH /todos/{id} — 更新 Todo
# ========================================================================

class TestUpdateTodo:

    async def test_update_todo_title(self, auth_client: AsyncClient):
        """更新标题"""
        create_resp = await auth_client.post("/todos/", json={"title": "旧标题", "description": "描述"})
        todo_id = create_resp.json()["id"]

        response = await auth_client.patch(f"/todos/{todo_id}", json={"title": "新标题"})

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "新标题"
        assert data["description"] == "描述"

    async def test_update_todo_mark_completed(self, auth_client: AsyncClient):
        """标记完成"""
        create_resp = await auth_client.post("/todos/", json={"title": "待完成"})
        todo_id = create_resp.json()["id"]

        response = await auth_client.patch(f"/todos/{todo_id}", json={"is_completed": True})

        assert response.status_code == 200
        assert response.json()["is_completed"] is True

    async def test_update_todo_priority(self, auth_client: AsyncClient):
        """更新优先级"""
        create_resp = await auth_client.post("/todos/", json={"title": "任务"})
        todo_id = create_resp.json()["id"]

        response = await auth_client.patch(f"/todos/{todo_id}", json={"priority": 3})

        assert response.status_code == 200
        assert response.json()["priority"] == 3

    async def test_update_todo_not_found(self, auth_client: AsyncClient):
        """更新不存在的返回 404"""
        response = await auth_client.patch("/todos/999", json={"title": "无效"})
        assert response.status_code == 404


# ========================================================================
# DELETE /todos/{id} — 删除 Todo
# ========================================================================

class TestDeleteTodo:

    async def test_delete_todo_success(self, auth_client: AsyncClient):
        """正常删除"""
        create_resp = await auth_client.post("/todos/", json={"title": "要删除的"})
        todo_id = create_resp.json()["id"]

        response = await auth_client.delete(f"/todos/{todo_id}")
        assert response.status_code == 204

        # 确认已删除
        get_resp = await auth_client.get(f"/todos/{todo_id}")
        assert get_resp.status_code == 404

    async def test_delete_todo_not_found(self, auth_client: AsyncClient):
        """删除不存在的返回 404"""
        response = await auth_client.delete("/todos/999")
        assert response.status_code == 404


# ========================================================================
# GET /health — 健康检查（不需要登录）
# ========================================================================

class TestHealthCheck:

    async def test_health_check(self, client: AsyncClient):
        """健康检查不需要 token"""
        response = await client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
