from httpx import AsyncClient

from tests.helpers import create_workspace


async def _register_and_login_with_id(
    client: AsyncClient,
    username: str,
) -> tuple[int, dict[str, str]]:
    password = "secret123"
    register_resp = await client.post(
        "/auth/register",
        json={"username": username, "password": password},
    )
    assert register_resp.status_code == 201
    user_id = register_resp.json()["id"]

    login_resp = await client.post(
        "/auth/login",
        data={"username": username, "password": password},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return user_id, {"Authorization": f"Bearer {token}"}


class TestWorkspacePermissions:
    async def test_member_cannot_manage_members(self, client: AsyncClient):
        owner_id, owner_headers = await _register_and_login_with_id(client, "owner1")
        member_id, member_headers = await _register_and_login_with_id(client, "member1")
        other_id, _ = await _register_and_login_with_id(client, "other1")

        workspace_id = await create_workspace(client, owner_headers, name="team-alpha")

        add_resp = await client.post(
            f"/workspaces/{workspace_id}/members",
            json={"user_id": member_id, "role": "member"},
            headers=owner_headers,
        )
        assert add_resp.status_code == 201

        member_add_resp = await client.post(
            f"/workspaces/{workspace_id}/members",
            json={"user_id": other_id, "role": "member"},
            headers=member_headers,
        )
        assert member_add_resp.status_code == 403

        member_patch_resp = await client.patch(
            f"/workspaces/{workspace_id}/members/{owner_id}",
            json={"role": "member"},
            headers=member_headers,
        )
        assert member_patch_resp.status_code == 403

        member_delete_resp = await client.delete(
            f"/workspaces/{workspace_id}/members/{owner_id}",
            headers=member_headers,
        )
        assert member_delete_resp.status_code == 403

    async def test_cannot_demote_last_owner(self, client: AsyncClient):
        owner_id, owner_headers = await _register_and_login_with_id(client, "owner2")
        workspace_id = await create_workspace(client, owner_headers, name="team-beta")

        resp = await client.patch(
            f"/workspaces/{workspace_id}/members/{owner_id}",
            json={"role": "admin"},
            headers=owner_headers,
        )
        assert resp.status_code == 400
