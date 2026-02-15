# Todo API

FastAPI-based Todo API with JWT auth and Team Collaboration V2.

## Stack

- Python 3.13
- FastAPI
- SQLAlchemy Async + SQLite (`aiosqlite`)
- Alembic
- Pytest + pytest-asyncio

## Run

```bash
pip install -r requirements-dev.txt
alembic upgrade head
python -m uvicorn app.main:app --app-dir src --reload --port 8000
```

## Auth

- `POST /auth/register`
- `POST /auth/login`

Use `Authorization: Bearer <access_token>` for protected endpoints.

## V2 API

### Workspaces

- `POST /workspaces`
- `GET /workspaces`
- `GET /workspaces/{workspace_id}`
- `POST /workspaces/{workspace_id}/members`
- `PATCH /workspaces/{workspace_id}/members/{user_id}`
- `DELETE /workspaces/{workspace_id}/members/{user_id}`

### Projects

- `POST /workspaces/{workspace_id}/projects`
- `GET /workspaces/{workspace_id}/projects`
- `GET /workspaces/{workspace_id}/projects/{project_id}`
- `PATCH /workspaces/{workspace_id}/projects/{project_id}`
- `DELETE /workspaces/{workspace_id}/projects/{project_id}`

### Tasks

- `POST /workspaces/{workspace_id}/projects/{project_id}/tasks`
- `GET /workspaces/{workspace_id}/tasks`
- `GET /workspaces/{workspace_id}/tasks/{task_id}`
- `PATCH /workspaces/{workspace_id}/tasks/{task_id}`
- `POST /workspaces/{workspace_id}/tasks/{task_id}/status-transitions`
- `DELETE /workspaces/{workspace_id}/tasks/{task_id}`

`GET /workspaces/{workspace_id}/tasks` supports `skip/limit`, `sort_by/sort_order`, and filters: `status`, `assignee_id`, `tag`, `due_at_from`, `due_at_to`.

### Comments / Tags / Watchers

- `POST /workspaces/{workspace_id}/tasks/{task_id}/comments`
- `GET /workspaces/{workspace_id}/tasks/{task_id}/comments`
- `PATCH /workspaces/{workspace_id}/tasks/{task_id}/comments/{comment_id}`
- `DELETE /workspaces/{workspace_id}/tasks/{task_id}/comments/{comment_id}`
- `POST /workspaces/{workspace_id}/tasks/{task_id}/tags`
- `DELETE /workspaces/{workspace_id}/tasks/{task_id}/tags/{tag}`
- `POST /workspaces/{workspace_id}/tasks/{task_id}/watchers`
- `DELETE /workspaces/{workspace_id}/tasks/{task_id}/watchers/{user_id}`

### Audit

- `GET /workspaces/{workspace_id}/audit-logs`

## Legacy `/todos` Endpoints

Legacy `/todos` endpoints are removed from the default app routing in V2.
After Phase C, the `todos` table is also dropped, so use V2 task endpoints.

## Migration Phases

- `64acdc31bcad`: Phase A, add collaboration schema
- `75d651717369`: Phase B, migrate `todos -> tasks`
- `921743ddcb91`: Phase C, drop `todos`

Commands:

```bash
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

## Test

```bash
pytest -q
```

Tests run against Alembic `head` schema and include V2 permission/state/idempotency/filter checks plus migration smoke checks.
