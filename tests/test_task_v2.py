from datetime import UTC, datetime, timedelta

from httpx import AsyncClient

from tests.helpers import register_and_login_with_id as _register_login


async def _create_workspace_project(
    client: AsyncClient,
    headers: dict[str, str],
    workspace_name: str,
    project_name: str,
) -> tuple[int, int]:
    workspace_resp = await client.post(
        "/workspaces",
        json={"name": workspace_name},
        headers=headers,
    )
    assert workspace_resp.status_code == 201
    workspace_id = workspace_resp.json()["id"]

    project_resp = await client.post(
        f"/workspaces/{workspace_id}/projects",
        json={"name": project_name},
        headers=headers,
    )
    assert project_resp.status_code == 201
    project_id = project_resp.json()["id"]

    return workspace_id, project_id


class TestTaskV2:
    async def test_cross_workspace_access_denied(self, client: AsyncClient):
        _, alice_headers = await _register_login(client, "alice_v2")
        _, bob_headers = await _register_login(client, "bob_v2")

        workspace_id, project_id = await _create_workspace_project(
            client,
            alice_headers,
            "alice-space",
            "alice-project",
        )

        create_resp = await client.post(
            f"/workspaces/{workspace_id}/projects/{project_id}/tasks",
            json={"title": "secret-task"},
            headers=alice_headers,
        )
        assert create_resp.status_code == 201
        task_id = create_resp.json()["id"]

        bob_get = await client.get(
            f"/workspaces/{workspace_id}/tasks/{task_id}",
            headers=bob_headers,
        )
        assert bob_get.status_code == 404

        bob_patch = await client.patch(
            f"/workspaces/{workspace_id}/tasks/{task_id}",
            json={"version": 1, "title": "hack"},
            headers=bob_headers,
        )
        assert bob_patch.status_code == 404

        bob_delete = await client.delete(
            f"/workspaces/{workspace_id}/tasks/{task_id}",
            headers=bob_headers,
        )
        assert bob_delete.status_code == 404

    async def test_illegal_status_transition_returns_400(self, client: AsyncClient):
        _, headers = await _register_login(client, "transition_user")
        workspace_id, project_id = await _create_workspace_project(
            client,
            headers,
            "transition-space",
            "transition-project",
        )

        create_resp = await client.post(
            f"/workspaces/{workspace_id}/projects/{project_id}/tasks",
            json={"title": "todo-task"},
            headers=headers,
        )
        task_id = create_resp.json()["id"]

        transition_resp = await client.post(
            f"/workspaces/{workspace_id}/tasks/{task_id}/status-transitions",
            json={"to_status": "done"},
            headers=headers,
        )
        assert transition_resp.status_code == 400

    async def test_optimistic_lock_conflict_returns_409(self, client: AsyncClient):
        _, headers = await _register_login(client, "version_user")
        workspace_id, project_id = await _create_workspace_project(
            client,
            headers,
            "version-space",
            "version-project",
        )

        create_resp = await client.post(
            f"/workspaces/{workspace_id}/projects/{project_id}/tasks",
            json={"title": "lock-task"},
            headers=headers,
        )
        task_id = create_resp.json()["id"]

        first_patch = await client.patch(
            f"/workspaces/{workspace_id}/tasks/{task_id}",
            json={"version": 1, "title": "lock-task-v2"},
            headers=headers,
        )
        assert first_patch.status_code == 200
        assert first_patch.json()["version"] == 2

        stale_patch = await client.patch(
            f"/workspaces/{workspace_id}/tasks/{task_id}",
            json={"version": 1, "title": "stale-write"},
            headers=headers,
        )
        assert stale_patch.status_code == 409

    async def test_idempotency_retry_and_conflict(self, client: AsyncClient):
        _, headers = await _register_login(client, "idempotent_user")
        workspace_id, project_id = await _create_workspace_project(
            client,
            headers,
            "idem-space",
            "idem-project",
        )

        key = "same-key"
        first = await client.post(
            f"/workspaces/{workspace_id}/projects/{project_id}/tasks",
            json={"title": "idempotent-task"},
            headers={**headers, "Idempotency-Key": key},
        )
        assert first.status_code == 201

        replay = await client.post(
            f"/workspaces/{workspace_id}/projects/{project_id}/tasks",
            json={"title": "idempotent-task"},
            headers={**headers, "Idempotency-Key": key},
        )
        assert replay.status_code == 201
        assert replay.json()["id"] == first.json()["id"]

        conflict = await client.post(
            f"/workspaces/{workspace_id}/projects/{project_id}/tasks",
            json={"title": "different-payload"},
            headers={**headers, "Idempotency-Key": key},
        )
        assert conflict.status_code == 409

    async def test_tag_uniqueness_enforced(self, client: AsyncClient):
        _, headers = await _register_login(client, "tag_user")
        workspace_id, project_id = await _create_workspace_project(
            client,
            headers,
            "tag-space",
            "tag-project",
        )

        create_resp = await client.post(
            f"/workspaces/{workspace_id}/projects/{project_id}/tasks",
            json={"title": "tag-task"},
            headers=headers,
        )
        task_id = create_resp.json()["id"]

        add_tag = await client.post(
            f"/workspaces/{workspace_id}/tasks/{task_id}/tags",
            json={"tag": "urgent"},
            headers=headers,
        )
        assert add_tag.status_code == 201

        add_duplicate_tag = await client.post(
            f"/workspaces/{workspace_id}/tasks/{task_id}/tags",
            json={"tag": "urgent"},
            headers=headers,
        )
        assert add_duplicate_tag.status_code == 409

    async def test_list_filters_combination(self, client: AsyncClient):
        assignee_id, headers = await _register_login(client, "filter_user")

        workspace_id, project_id = await _create_workspace_project(
            client,
            headers,
            "filter-space",
            "filter-project",
        )

        now = datetime.now(UTC)
        due_match = (now + timedelta(days=2)).isoformat()
        due_other = (now + timedelta(days=10)).isoformat()

        t1 = await client.post(
            f"/workspaces/{workspace_id}/projects/{project_id}/tasks",
            json={"title": "match-task", "assignee_id": assignee_id, "due_at": due_match},
            headers=headers,
        )
        assert t1.status_code == 201
        task_match_id = t1.json()["id"]

        t2 = await client.post(
            f"/workspaces/{workspace_id}/projects/{project_id}/tasks",
            json={"title": "other-task", "assignee_id": assignee_id, "due_at": due_other},
            headers=headers,
        )
        assert t2.status_code == 201

        t3 = await client.post(
            f"/workspaces/{workspace_id}/projects/{project_id}/tasks",
            json={"title": "non-assignee", "due_at": due_match},
            headers=headers,
        )
        assert t3.status_code == 201

        trans = await client.post(
            f"/workspaces/{workspace_id}/tasks/{task_match_id}/status-transitions",
            json={"to_status": "in_progress"},
            headers=headers,
        )
        assert trans.status_code == 200

        add_tag_match = await client.post(
            f"/workspaces/{workspace_id}/tasks/{task_match_id}/tags",
            json={"tag": "urgent"},
            headers=headers,
        )
        assert add_tag_match.status_code == 201

        add_tag_other = await client.post(
            f"/workspaces/{workspace_id}/tasks/{t2.json()['id']}/tags",
            json={"tag": "urgent"},
            headers=headers,
        )
        assert add_tag_other.status_code == 201

        from_date = (now + timedelta(days=1)).isoformat()
        to_date = (now + timedelta(days=3)).isoformat()

        list_resp = await client.get(
            f"/workspaces/{workspace_id}/tasks",
            params={
                "status": "in_progress",
                "assignee_id": assignee_id,
                "tag": "urgent",
                "due_at_from": from_date,
                "due_at_to": to_date,
            },
            headers=headers,
        )
        assert list_resp.status_code == 200
        payload = list_resp.json()
        assert payload["total"] == 1
        assert len(payload["items"]) == 1
        assert payload["items"][0]["id"] == task_match_id
