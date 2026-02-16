# API 契约维护快照

## 文档定位
这是一份“维护视角”的 API 合同，不是 Swagger 替代品。  
目标：让维护者快速确认接口边界、约束和变更影响。

## 基础信息
- 本地地址：`http://localhost:8000`
- Swagger：`GET /docs`
- 健康检查：`GET /health`

## 认证约定
- 认证方式：JWT Bearer
- 请求头：
```text
Authorization: Bearer <access_token>
```
- 登录接口：`POST /auth/login`（OAuth2 password form）

## 通用返回码语义
| 状态码 | 语义 |
|---|---|
| `200` | 查询/更新成功 |
| `201` | 创建成功 |
| `204` | 删除成功，无响应体 |
| `400` | 业务规则不满足（如非法状态流转） |
| `401` | 未认证或 token 无效 |
| `403` | 已认证但权限不足 |
| `404` | 资源不存在或不可见 |
| `409` | 资源冲突（幂等、版本、唯一键） |
| `422` | 参数校验失败 |

## 分页契约
列表分页返回统一结构：
```json
{
  "items": [],
  "total": 0,
  "skip": 0,
  "limit": 20
}
```

## 业务域端点总览

### Auth
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

### Workspaces
- `POST /workspaces`
- `GET /workspaces`
- `GET /workspaces/{workspace_id}`
- `GET /workspaces/{workspace_id}/members`
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

任务列表查询参数：
- `skip`, `limit`
- `sort_by`, `sort_order`
- `status`, `assignee_id`, `project_id`, `tag`
- `due_at_from`, `due_at_to`

### Collaboration
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

## 特殊协议（必须关注）

### 幂等创建（Task）
- 端点：`POST /workspaces/{workspace_id}/projects/{project_id}/tasks`
- 请求头：`Idempotency-Key: <string>`
- 约束：同用户 + 同路由 + 同 key + 同请求体，可重放同一结果。

### 乐观并发控制（Task）
- 端点：`PATCH /workspaces/{workspace_id}/tasks/{task_id}`
- 请求体必须包含 `version`
- 若版本过期，返回 `409`

## RBAC 约束
- 大部分端点需要登录用户。
- 所有资源以 workspace 为作用域，必须先验证 membership。
- 高权限操作（owner/admin）包括：
  - workspace 成员管理
  - audit 日志访问

## 变更影响检查单
接口变更时至少同步以下四项：
1. `src/app/schemas/*`（契约）
2. `tests/*`（回归）
3. `docs/maintenance/10-api-contract.md`（本文件）
4. `README.md` API 端点章节

## 快速回归建议
- 合同变更后至少跑：
```bash
pytest -q
python -m mypy
```
- 前端受影响时加跑：
```bash
cd frontend && npm run test
```
