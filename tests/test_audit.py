from httpx import AsyncClient

from tests.helpers import register_and_login_with_id as _register_login


class TestAuditLogs:
    async def test_audit_logs_owner_admin_only(self, client: AsyncClient):
        owner_id, owner_headers = await _register_login(client, "audit_owner")
        member_id, member_headers = await _register_login(client, "audit_member")

        ws_resp = await client.post(
            "/workspaces",
            json={"name": "audit-space"},
            headers=owner_headers,
        )
        assert ws_resp.status_code == 201
        workspace_id = ws_resp.json()["id"]

        add_member_resp = await client.post(
            f"/workspaces/{workspace_id}/members",
            json={"user_id": member_id, "role": "member"},
            headers=owner_headers,
        )
        assert add_member_resp.status_code == 201

        project_resp = await client.post(
            f"/workspaces/{workspace_id}/projects",
            json={"name": "audit-project"},
            headers=owner_headers,
        )
        assert project_resp.status_code == 201
        project_id = project_resp.json()["id"]

        task_resp = await client.post(
            f"/workspaces/{workspace_id}/projects/{project_id}/tasks",
            json={"title": "audit-task"},
            headers=owner_headers,
        )
        assert task_resp.status_code == 201

        member_audit = await client.get(
            f"/workspaces/{workspace_id}/audit-logs",
            headers=member_headers,
        )
        assert member_audit.status_code == 403

        owner_audit = await client.get(
            f"/workspaces/{workspace_id}/audit-logs",
            headers=owner_headers,
        )
        assert owner_audit.status_code == 200
        payload = owner_audit.json()
        assert payload["total"] >= 3
        assert len(payload["items"]) >= 1

        assert owner_id > 0
