import pytest
from httpx import AsyncClient


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("post", "/todos/", {"title": "legacy"}),
        ("get", "/todos/", None),
        ("get", "/todos/1", None),
        ("patch", "/todos/1", {"title": "updated"}),
        ("delete", "/todos/1", None),
    ],
)
async def test_legacy_todo_endpoints_removed(
    client: AsyncClient,
    auth_client: AsyncClient,
    method: str,
    path: str,
    payload: dict | None,
) -> None:
    request_kwargs = {"json": payload} if payload is not None else {}
    anonymous_response = await client.request(method.upper(), path, **request_kwargs)
    auth_response = await auth_client.request(method.upper(), path, **request_kwargs)

    assert anonymous_response.status_code == 404
    assert auth_response.status_code == 404


async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
