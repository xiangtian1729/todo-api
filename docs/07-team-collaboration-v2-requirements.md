# Todo API V2 需求文档（团队协作版）

> 文档类型：可执行需求规范（PRD + 技术任务拆解）
>  
> 适用项目：`todo-api`（Python 3.13 + FastAPI + Async SQLAlchemy + SQLite + Alembic + Pytest）
>  
> 版本：v1.0
>  
> 状态：Ready for Implementation

---

## 1. 背景与目标

当前项目已具备单用户 Todo 的认证、CRUD、测试与迁移能力。下一阶段目标是将系统升级为**团队协作任务系统**，提高业务复杂度，同时保持安全性、可维护性、可测试性与可回滚性。

### 1.1 业务目标

1. 支持团队（Workspace）内多人协作管理任务。
2. 支持角色权限控制（Owner/Admin/Member）。
3. 支持任务生命周期状态流转与操作审计。
4. 支持评论、关注、标签等协作能力。
5. 保持 API 安全与数据隔离，防止跨用户/跨团队访问（IDOR）。

### 1.2 成功指标（发布后）

1. 所有核心接口自动化测试通过率 100%。
2. 权限与数据隔离相关测试覆盖率 >= 95%。
3. 关键业务路径（创建任务、指派、状态流转、评论）无 P0/P1 缺陷。
4. 数据库迁移可正向升级与单步回滚。

---

## 2. 范围定义

### 2.1 本期范围（In Scope）

1. 多租户模型：Workspace、Membership、Project、Task。
2. 角色权限：Owner/Admin/Member。
3. 任务状态机：`todo -> in_progress -> blocked -> done`。
4. 任务协作：评论、标签、关注者（watchers）。
5. 审计日志：记录关键操作（创建/更新/删除/状态变更/成员变更）。
6. 幂等创建（Idempotency-Key）与乐观锁（version）。
7. 查询能力：分页、排序、过滤（状态、负责人、标签、截止时间）。

### 2.2 非本期范围（Out of Scope）

1. 实时推送（WebSocket）。
2. 邮件/短信通知。
3. 文件附件上传。
4. 第三方 OAuth 登录。

---

## 3. 角色与权限模型

### 3.1 角色定义

1. `owner`：工作区所有权限，含成员管理与删除项目。
2. `admin`：可管理项目与任务，不可转移 workspace 所有权。
3. `member`：可读写被授权项目内任务，不可管理成员。

### 3.2 权限矩阵（核心）

1. Workspace 成员管理：`owner/admin` 可操作，`member` 禁止。
2. Project 创建/编辑：`owner/admin` 可操作，`member` 只读。
3. Task 创建：`owner/admin/member`（需在项目成员范围内）。
4. Task 删除：创建者、负责人、或 `owner/admin`。
5. Task 状态流转：创建者、负责人、或 `owner/admin`。
6. 评论：项目成员可增删改（仅可改/删自己评论，`owner/admin` 可删全部）。

---

## 4. 核心业务规则

### 4.1 数据隔离规则（强制）

1. 所有查询必须先按 `workspace_id` 过滤，再按权限过滤。
2. 所有资源访问必须验证 `current_user` 是否为该 workspace 成员。
3. 禁止通过全局 ID 直接读取跨 workspace 资源。

### 4.2 任务状态机

允许状态：

1. `todo`
2. `in_progress`
3. `blocked`
4. `done`

允许流转：

1. `todo -> in_progress`
2. `in_progress -> blocked`
3. `blocked -> in_progress`
4. `in_progress -> done`
5. `done -> in_progress`（允许返工）

禁止流转：

1. `todo -> done`
2. `blocked -> done`

### 4.3 幂等与并发控制

1. `POST /tasks` 支持请求头 `Idempotency-Key`（同用户+同 key+同路由在 24h 内返回同一结果）。
2. `PATCH /tasks/{id}` 需携带 `version`，版本不一致返回 `409 CONFLICT`。

---

## 5. 数据模型设计

> 说明：以下是业务字段与约束要求，实际落库通过 Alembic 迁移，不使用 `Base.metadata.create_all`。

### 5.1 新增实体

1. `workspaces`
2. `workspace_memberships`
3. `projects`
4. `tasks`（替代原有 `todos`）
5. `task_comments`
6. `task_tags`
7. `task_watchers`
8. `audit_logs`
9. `idempotency_keys`

### 5.2 字段与关键约束

1. `workspace_memberships` 唯一键：`(workspace_id, user_id)`。
2. `projects` 唯一键：`(workspace_id, name)`。
3. `tasks` 索引：`(workspace_id, project_id, status, assignee_id, due_at)`。
4. `task_tags` 唯一键：`(task_id, tag)`。
5. `task_watchers` 唯一键：`(task_id, user_id)`。
6. `audit_logs` 索引：`(workspace_id, entity_type, entity_id, created_at)`。
7. `tasks.version` 默认为 1，每次更新 +1。

### 5.3 与现有模型关系

1. 保留 `users` 表。
2. `todos` 表迁移为 `tasks`（见第 10 章迁移策略）。

---

## 6. API 需求清单（V2）

## 6.1 Workspace

1. `POST /workspaces`：创建 workspace。
2. `GET /workspaces`：列出当前用户可见 workspace。
3. `GET /workspaces/{workspace_id}`：workspace 详情。
4. `POST /workspaces/{workspace_id}/members`：添加成员（owner/admin）。
5. `PATCH /workspaces/{workspace_id}/members/{user_id}`：修改角色（owner/admin）。
6. `DELETE /workspaces/{workspace_id}/members/{user_id}`：移除成员（owner/admin）。

## 6.2 Projects

1. `POST /workspaces/{workspace_id}/projects`
2. `GET /workspaces/{workspace_id}/projects`
3. `GET /workspaces/{workspace_id}/projects/{project_id}`
4. `PATCH /workspaces/{workspace_id}/projects/{project_id}`
5. `DELETE /workspaces/{workspace_id}/projects/{project_id}`

## 6.3 Tasks

1. `POST /workspaces/{workspace_id}/projects/{project_id}/tasks`
2. `GET /workspaces/{workspace_id}/tasks`（支持过滤、排序、分页）
3. `GET /workspaces/{workspace_id}/tasks/{task_id}`
4. `PATCH /workspaces/{workspace_id}/tasks/{task_id}`
5. `POST /workspaces/{workspace_id}/tasks/{task_id}/status-transitions`
6. `DELETE /workspaces/{workspace_id}/tasks/{task_id}`

## 6.4 Comments / Tags / Watchers

1. `POST /workspaces/{workspace_id}/tasks/{task_id}/comments`
2. `GET /workspaces/{workspace_id}/tasks/{task_id}/comments`
3. `PATCH /workspaces/{workspace_id}/tasks/{task_id}/comments/{comment_id}`
4. `DELETE /workspaces/{workspace_id}/tasks/{task_id}/comments/{comment_id}`
5. `POST /workspaces/{workspace_id}/tasks/{task_id}/tags`
6. `DELETE /workspaces/{workspace_id}/tasks/{task_id}/tags/{tag}`
7. `POST /workspaces/{workspace_id}/tasks/{task_id}/watchers`
8. `DELETE /workspaces/{workspace_id}/tasks/{task_id}/watchers/{user_id}`

## 6.5 Audit

1. `GET /workspaces/{workspace_id}/audit-logs`

### 6.6 返回码规范

1. `200/201/204`：成功。
2. `400`：非法状态流转或参数错误。
3. `401`：未认证。
4. `403`：无权限。
5. `404`：资源不存在或不可见（避免泄漏存在性时可统一 404）。
6. `409`：版本冲突或幂等冲突。
7. `422`：Pydantic 参数校验失败。

---

## 7. Schema 设计要求（Pydantic）

1. 所有请求与响应必须使用独立 Schema，禁止直接返回 ORM 模型。
2. 更新接口使用 `exclude_unset=True` 进行部分更新。
3. 所有输入字段定义边界（`min_length/max_length/ge/le`）。
4. 列表接口返回统一分页结构：
   `{"items": [...], "total": <int>, "skip": <int>, "limit": <int>}`。

---

## 8. 安全要求

1. JWT 鉴权沿用现有机制，不变更核心签发逻辑。
2. 所有业务操作必须依赖 `current_user`。
3. 所有数据库查询必须优先按 `workspace_id` + `membership` 限制。
4. 审计日志记录：
   `actor_user_id`, `workspace_id`, `entity_type`, `entity_id`, `action`, `changes`。
5. 不在日志中记录敏感信息（密码、token、密钥）。

---

## 9. 非功能需求

1. 代码风格：保持现有项目结构（`src/app`、`tests`、`migrations`）。
2. 性能：列表接口默认 `limit=20`，最大 `limit=100`。
3. 可维护性：路由层只做参数编排，复杂逻辑下沉到 `services/`（新增）。
4. 可观测性：关键业务动作有结构化日志与审计日志。

---

## 10. 数据库迁移策略（Alembic）

## 10.1 迁移原则

1. 仅通过 Alembic 管理 Schema。
2. 每次模型变更必须附带迁移脚本与回滚路径。
3. 破坏性变更分两步执行（先兼容，再清理）。

## 10.2 迁移阶段

### Phase A（并存期）

1. 新建 V2 表：`workspaces`、`projects`、`tasks` 等。
2. 保留 `todos`，不立即删除。
3. 应用层写入新表，读取可双读（过渡期）。

### Phase B（切换期）

1. 完成历史 `todos -> tasks` 数据迁移。
2. 验证数据完整性与数量一致性。

### Phase C（清理期）

1. 删除旧表 `todos` 及相关无用索引。

## 10.3 Alembic 命令模板

```bash
alembic revision --autogenerate -m "add workspace project task v2 schema"
alembic upgrade head
alembic downgrade -1
```

---

## 11. 测试需求（Pytest + AsyncIO）

### 11.1 测试层级

1. 单元测试：状态机、权限判定、版本冲突逻辑。
2. 接口测试：认证、CRUD、过滤、分页、排序。
3. 安全测试：跨 workspace 越权读取/修改/删除必须失败。
4. 迁移测试：`upgrade -> downgrade -> upgrade` 可执行。

### 11.2 必测场景清单（最小完整）

1. 用户 A 无法读取用户 B 所在 workspace 任务。
2. `member` 无法管理成员。
3. 非法状态流转返回 `400`。
4. 并发更新同一任务，低版本更新返回 `409`。
5. 同 `Idempotency-Key` 重试返回同一 task。
6. 标签去重约束生效。
7. 评论权限（仅作者可编辑，owner/admin 可删除）。
8. 列表过滤组合：`status + assignee + due_at`。

---

## 12. 任务拆解（可执行）

> 估算单位：人天（PD）

### Epic 1：领域模型与迁移（5 PD）

1. 建立 V2 ORM 模型与关系（2 PD）。
2. 编写 Alembic 初始 V2 迁移（1 PD）。
3. 编写 `todos -> tasks` 数据迁移脚本（1 PD）。
4. 编写回滚脚本与校验脚本（1 PD）。

### Epic 2：权限与工作区能力（4 PD）

1. Workspace/Membership API（2 PD）。
2. 角色校验依赖与复用工具函数（1 PD）。
3. 权限测试与越权测试（1 PD）。

### Epic 3：项目与任务核心流程（6 PD）

1. Project CRUD（1.5 PD）。
2. Task CRUD + 过滤分页排序（2 PD）。
3. 状态机流转接口（1 PD）。
4. 乐观锁 version 机制（1 PD）。
5. 幂等键机制（0.5 PD）。

### Epic 4：协作能力（4 PD）

1. 评论 API（1.5 PD）。
2. 标签与关注者 API（1.5 PD）。
3. 对应鉴权与测试（1 PD）。

### Epic 5：审计与可观测性（2 PD）

1. 审计日志写入与查询 API（1 PD）。
2. 关键业务日志补齐（1 PD）。

### Epic 6：测试与验收（4 PD）

1. 完整测试补齐（2.5 PD）。
2. CI 校验增强（0.5 PD）。
3. 回归测试与发布验收（1 PD）。

**总计：25 PD（1 人约 5 周，2 人约 2.5 周）**

---

## 13. 里程碑计划

1. M1（第 1 周末）：完成 V2 表结构与迁移脚本。
2. M2（第 2 周末）：完成 Workspace/Project/Task 主流程。
3. M3（第 3 周末）：完成评论/标签/关注者与审计。
4. M4（第 4 周末）：完成全量测试与上线准备。

---

## 14. 验收标准（Definition of Done）

1. 所有 API 文档在 `/docs` 可见且与实现一致。
2. `pytest -q` 全绿，新增测试覆盖核心规则与越权场景。
3. `alembic upgrade head`、`alembic downgrade -1` 可执行。
4. 不存在跨 workspace 数据读取/修改漏洞。
5. 幂等与版本冲突行为符合规范。
6. README/变更说明更新完毕。

---

## 15. 风险与应对

1. SQLite 并发写限制导致锁冲突：
   在测试中模拟并发并控制事务粒度，必要时短事务+重试策略。
2. 迁移风险导致数据不一致：
   分阶段迁移，先并存后切换，提供行数与校验脚本。
3. 权限逻辑复杂易遗漏：
   统一权限依赖函数，禁止路由内临时判断散落。
4. 范围膨胀：
   坚持本期 Out of Scope，不追加通知/附件等功能。

---

## 16. 交付物清单

1. 代码：
   `src/app/models/`, `src/app/schemas/`, `src/app/routers/`, `src/app/services/`（新增）。
2. 迁移：
   `migrations/versions/*_v2_*.py`。
3. 测试：
   `tests/test_workspace.py`, `tests/test_project.py`, `tests/test_task_v2.py`, `tests/test_permissions.py`, `tests/test_audit.py`。
4. 文档：
   `README.md`（V2 接口）、本需求文档、迁移操作说明。

---

## 17. 开发启动清单（执行顺序）

1. 建分支：`feat/v2-team-collaboration`。
2. 建立 V2 模型与 Schema 草稿。
3. 生成并审查 Alembic 迁移。
4. 先写权限与状态机测试（红灯）。
5. 实现 Workspace/Project/Task 主流程（转绿）。
6. 实现评论/标签/关注者。
7. 接入审计日志。
8. 全量回归、修复、文档更新。
9. 提交 PR，附迁移与回滚说明。

