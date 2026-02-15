from httpx import AsyncClient

from tests.helpers import register_and_login_with_id as _register_login


class TestCommentPermissions:
    async def test_comment_author_edit_and_owner_delete_any(self, client: AsyncClient):
        owner_id, owner_headers = await _register_login(client, "comment_owner")
        member_id, member_headers = await _register_login(client, "comment_member")

        ws_resp = await client.post(
            "/workspaces",
            json={"name": "comment-space"},
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
            json={"name": "comment-project"},
            headers=owner_headers,
        )
        assert project_resp.status_code == 201
        project_id = project_resp.json()["id"]

        task_resp = await client.post(
            f"/workspaces/{workspace_id}/projects/{project_id}/tasks",
            json={"title": "comment-task"},
            headers=owner_headers,
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        member_comment = await client.post(
            f"/workspaces/{workspace_id}/tasks/{task_id}/comments",
            json={"content": "member-comment"},
            headers=member_headers,
        )
        assert member_comment.status_code == 201
        member_comment_id = member_comment.json()["id"]

        owner_comment = await client.post(
            f"/workspaces/{workspace_id}/tasks/{task_id}/comments",
            json={"content": "owner-comment"},
            headers=owner_headers,
        )
        assert owner_comment.status_code == 201
        owner_comment_id = owner_comment.json()["id"]

        owner_edit_member = await client.patch(
            f"/workspaces/{workspace_id}/tasks/{task_id}/comments/{member_comment_id}",
            json={"content": "owner-edit"},
            headers=owner_headers,
        )
        assert owner_edit_member.status_code == 403

        member_edit_own = await client.patch(
            f"/workspaces/{workspace_id}/tasks/{task_id}/comments/{member_comment_id}",
            json={"content": "member-edit"},
            headers=member_headers,
        )
        assert member_edit_own.status_code == 200
        assert member_edit_own.json()["content"] == "member-edit"

        member_delete_owner = await client.delete(
            f"/workspaces/{workspace_id}/tasks/{task_id}/comments/{owner_comment_id}",
            headers=member_headers,
        )
        assert member_delete_owner.status_code == 403

        owner_delete_member = await client.delete(
            f"/workspaces/{workspace_id}/tasks/{task_id}/comments/{member_comment_id}",
            headers=owner_headers,
        )
        assert owner_delete_member.status_code == 204

        assert owner_id > 0
