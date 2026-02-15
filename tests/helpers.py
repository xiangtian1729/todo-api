from httpx import AsyncClient


async def register_and_login(
    client: AsyncClient,
    username: str,
    password: str = "secret123",
) -> dict[str, str]:
    register_resp = await client.post(
        "/auth/register",
        json={"username": username, "password": password},
    )
    assert register_resp.status_code == 201

    login_resp = await client.post(
        "/auth/login",
        data={"username": username, "password": password},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def register_and_login_with_id(
    client: AsyncClient,
    username: str,
    password: str = "secret123",
) -> tuple[int, dict[str, str]]:
    """Register and login, returning (user_id, auth_headers)."""
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


async def create_workspace(client: AsyncClient, headers: dict[str, str], name: str = "workspace") -> int:
    resp = await client.post("/workspaces", json={"name": name}, headers=headers)
    assert resp.status_code == 201
    return resp.json()["id"]


async def create_project(
    client: AsyncClient,
    headers: dict[str, str],
    workspace_id: int,
    name: str = "project",
) -> int:
    resp = await client.post(
        f"/workspaces/{workspace_id}/projects",
        json={"name": name},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def create_task(
    client: AsyncClient,
    headers: dict[str, str],
    workspace_id: int,
    project_id: int,
    title: str,
    **extra,
) -> int:
    payload = {"title": title, **extra}
    resp = await client.post(
        f"/workspaces/{workspace_id}/projects/{project_id}/tasks",
        json=payload,
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()["id"]
