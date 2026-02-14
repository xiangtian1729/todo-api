"""
Todo API 端点测试

这个文件测试所有 5 个 CRUD 端点，确保它们正常工作。

测试的基本结构叫 AAA 模式：
    Arrange（准备）→ 准备测试数据和环境
    Act（执行）    → 调用要测试的 API
    Assert（断言） → 检查结果是否符合预期

每个测试函数的命名规则：test_<操作>_<场景>
    例如：test_create_todo_success → 测试创建 Todo 成功的情况
"""

import pytest
from httpx import AsyncClient


# ========================================================================
# POST /todos/ — 创建 Todo 的测试
# ========================================================================

class TestCreateTodo:
    """测试创建 Todo 端点的各种场景"""

    async def test_create_todo_success(self, client: AsyncClient):
        """正常创建一个 Todo"""
        # Arrange: 准备请求数据
        payload = {"title": "学习 Python", "description": "完成第一章"}

        # Act: 发送 POST 请求
        response = await client.post("/todos/", json=payload)

        # Assert: 检查响应
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "学习 Python"
        assert data["description"] == "完成第一章"
        assert data["is_completed"] is False    # 默认未完成
        assert data["priority"] == 2            # 默认中优先级
        assert data["id"] is not None           # 应该有自动生成的 id
        assert data["created_at"] is not None   # 应该有创建时间

    async def test_create_todo_without_description(self, client: AsyncClient):
        """创建 Todo 时不写描述（描述是可选的）"""
        payload = {"title": "买菜"}

        response = await client.post("/todos/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "买菜"
        assert data["description"] is None      # 没写描述，应该为 None

    async def test_create_todo_empty_title_fails(self, client: AsyncClient):
        """标题为空应该失败（验证规则：min_length=1）"""
        payload = {"title": ""}

        response = await client.post("/todos/", json=payload)

        assert response.status_code == 422       # Pydantic 验证失败

    async def test_create_todo_missing_title_fails(self, client: AsyncClient):
        """不提供标题应该失败（标题是必填的）"""
        payload = {"description": "没有标题"}

        response = await client.post("/todos/", json=payload)

        assert response.status_code == 422

    async def test_create_todo_with_priority(self, client: AsyncClient):
        """创建时指定优先级"""
        payload = {"title": "紧急任务", "priority": 3}

        response = await client.post("/todos/", json=payload)

        assert response.status_code == 201
        assert response.json()["priority"] == 3

    async def test_create_todo_invalid_priority_fails(self, client: AsyncClient):
        """优先级超出范围应该失败（只允许 1-3）"""
        payload = {"title": "测试", "priority": 5}

        response = await client.post("/todos/", json=payload)

        assert response.status_code == 422


# ========================================================================
# GET /todos/ — 获取 Todo 列表的测试
# ========================================================================

class TestListTodos:
    """测试获取 Todo 列表端点"""

    async def test_list_todos_empty(self, client: AsyncClient):
        """数据库为空时，应该返回空列表"""
        response = await client.get("/todos/")

        assert response.status_code == 200
        assert response.json() == []

    async def test_list_todos_with_data(self, client: AsyncClient):
        """创建几个 Todo 后，应该返回它们"""
        # Arrange: 先创建 2 个 Todo
        await client.post("/todos/", json={"title": "Todo 1"})
        await client.post("/todos/", json={"title": "Todo 2"})

        # Act
        response = await client.get("/todos/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "Todo 1"
        assert data[1]["title"] == "Todo 2"

    async def test_list_todos_with_pagination(self, client: AsyncClient):
        """测试分页：使用 skip 和 limit 参数"""
        # Arrange: 创建 3 个 Todo
        for i in range(3):
            await client.post("/todos/", json={"title": f"Todo {i + 1}"})

        # Act: 跳过第 1 条，只取 1 条
        response = await client.get("/todos/", params={"skip": 1, "limit": 1})

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Todo 2"     # 跳过了 Todo 1


# ========================================================================
# GET /todos/{id} — 获取单个 Todo 的测试
# ========================================================================

class TestGetTodo:
    """测试获取单个 Todo 端点"""

    async def test_get_todo_success(self, client: AsyncClient):
        """正常获取一个已存在的 Todo"""
        # Arrange: 先创建一个 Todo
        create_resp = await client.post("/todos/", json={"title": "测试"})
        todo_id = create_resp.json()["id"]

        # Act
        response = await client.get(f"/todos/{todo_id}")

        # Assert
        assert response.status_code == 200
        assert response.json()["title"] == "测试"

    async def test_get_todo_not_found(self, client: AsyncClient):
        """获取不存在的 Todo，应该返回 404"""
        response = await client.get("/todos/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ========================================================================
# PATCH /todos/{id} — 更新 Todo 的测试
# ========================================================================

class TestUpdateTodo:
    """测试更新 Todo 端点"""

    async def test_update_todo_title(self, client: AsyncClient):
        """只更新标题，其他字段不变"""
        # Arrange
        create_resp = await client.post("/todos/", json={"title": "旧标题", "description": "描述"})
        todo_id = create_resp.json()["id"]

        # Act: 只发送新标题
        response = await client.patch(f"/todos/{todo_id}", json={"title": "新标题"})

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "新标题"
        assert data["description"] == "描述"     # 描述没变

    async def test_update_todo_mark_completed(self, client: AsyncClient):
        """标记 Todo 为已完成"""
        # Arrange
        create_resp = await client.post("/todos/", json={"title": "待完成"})
        todo_id = create_resp.json()["id"]

        # Act
        response = await client.patch(f"/todos/{todo_id}", json={"is_completed": True})

        # Assert
        assert response.status_code == 200
        assert response.json()["is_completed"] is True

    async def test_update_todo_not_found(self, client: AsyncClient):
        """更新不存在的 Todo，应该返回 404"""
        response = await client.patch("/todos/999", json={"title": "无效"})

        assert response.status_code == 404

    async def test_update_todo_priority(self, client: AsyncClient):
        """更新优先级"""
        # Arrange
        create_resp = await client.post("/todos/", json={"title": "任务"})
        todo_id = create_resp.json()["id"]

        # Act
        response = await client.patch(f"/todos/{todo_id}", json={"priority": 3})

        # Assert
        assert response.status_code == 200
        assert response.json()["priority"] == 3


# ========================================================================
# DELETE /todos/{id} — 删除 Todo 的测试
# ========================================================================

class TestDeleteTodo:
    """测试删除 Todo 端点"""

    async def test_delete_todo_success(self, client: AsyncClient):
        """正常删除一个 Todo"""
        # Arrange: 先创建一个 Todo
        create_resp = await client.post("/todos/", json={"title": "要删除的"})
        todo_id = create_resp.json()["id"]

        # Act
        response = await client.delete(f"/todos/{todo_id}")

        # Assert: 删除成功返回 204
        assert response.status_code == 204

        # 再次获取，应该返回 404（已被删除）
        get_response = await client.get(f"/todos/{todo_id}")
        assert get_response.status_code == 404

    async def test_delete_todo_not_found(self, client: AsyncClient):
        """删除不存在的 Todo，应该返回 404"""
        response = await client.delete("/todos/999")

        assert response.status_code == 404


# ========================================================================
# GET /health — 健康检查的测试
# ========================================================================

class TestHealthCheck:
    """测试健康检查端点"""

    async def test_health_check(self, client: AsyncClient):
        """健康检查应该返回正常状态"""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
