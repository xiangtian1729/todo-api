from httpx import AsyncClient

from tests.helpers import create_workspace, register_and_login_with_id as _register_login


class TestProjectPermissions:
    async def test_member_read_only_for_projects(self, client: AsyncClient):
        owner_id, owner_headers = await _register_login(client, "projowner")
        member_id, member_headers = await _register_login(client, "projmember")

        workspace_id = await create_workspace(client, owner_headers, name="project-space")

        add_member_resp = await client.post(
            f"/workspaces/{workspace_id}/members",
            json={"user_id": member_id, "role": "member"},
            headers=owner_headers,
        )
        assert add_member_resp.status_code == 201

        create_resp = await client.post(
            f"/workspaces/{workspace_id}/projects",
            json={"name": "backend"},
            headers=owner_headers,
        )
        assert create_resp.status_code == 201
        project_id = create_resp.json()["id"]

        member_create = await client.post(
            f"/workspaces/{workspace_id}/projects",
            json={"name": "frontend"},
            headers=member_headers,
        )
        assert member_create.status_code == 403

        member_get = await client.get(
            f"/workspaces/{workspace_id}/projects/{project_id}",
            headers=member_headers,
        )
        assert member_get.status_code == 200

        member_list = await client.get(
            f"/workspaces/{workspace_id}/projects",
            headers=member_headers,
        )
        assert member_list.status_code == 200
        assert len(member_list.json()) == 1

        member_patch = await client.patch(
            f"/workspaces/{workspace_id}/projects/{project_id}",
            json={"name": "renamed"},
            headers=member_headers,
        )
        assert member_patch.status_code == 403

        member_delete = await client.delete(
            f"/workspaces/{workspace_id}/projects/{project_id}",
            headers=member_headers,
        )
        assert member_delete.status_code == 403

        # keep lint tools from treating owner_id unused in strict configs
        assert owner_id > 0
