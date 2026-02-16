# Todo API

全栈任务管理应用 —— FastAPI 后端 + Next.js 前端。

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.13, FastAPI, SQLAlchemy Async, Alembic |
| 前端 | Next.js 16, Shadcn UI, TanStack Query, Zustand |
| 数据库 | SQLite (`aiosqlite`) |
| 部署 | Docker, Docker Compose, GitHub Actions CI |

## Quick Start

### 方式一：本地开发

```bash
# 后端
pip install -r requirements-dev.txt
alembic upgrade head
python -m uvicorn app.main:app --app-dir src --reload --port 8000
```

```bash
# 前端
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

- 后端 API 文档: http://localhost:8000/docs
- 前端: http://localhost:3000

### 方式二：Docker Compose（一键全栈）

```bash
docker-compose up --build
```

## 项目结构

```
todo-api/
├── src/app/                  # 后端源码
│   ├── routers/              #   API 路由层
│   ├── services/             #   业务逻辑层
│   ├── models/               #   SQLAlchemy 模型
│   ├── schemas/              #   Pydantic 请求/响应模型
│   ├── main.py               #   FastAPI 入口
│   ├── security.py           #   JWT 认证
│   └── database.py           #   数据库连接
├── migrations/               # Alembic 迁移
├── tests/                    # Pytest 后端测试
├── frontend/                 # Next.js 前端（详见 frontend/README.md）
├── docs/                     # 项目文档
├── Dockerfile                # 后端 Docker 镜像
├── docker-compose.yml        # 全栈编排
└── .github/workflows/ci.yml  # CI：lint + type check + test + frontend build
```

## API 端点（28 个）

### Auth

- `POST /auth/register` — 注册
- `POST /auth/login` — 登录，返回 JWT Token

使用 `Authorization: Bearer <access_token>` 访问受保护端点。

### Workspaces（6）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/workspaces` | 创建工作空间 |
| GET | `/workspaces` | 列出工作空间 |
| GET | `/workspaces/{wid}` | 工作空间详情 |
| POST | `/workspaces/{wid}/members` | 邀请成员 |
| PATCH | `/workspaces/{wid}/members/{uid}` | 修改角色 |
| DELETE | `/workspaces/{wid}/members/{uid}` | 移除成员 |

### Projects（5）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/workspaces/{wid}/projects` | 创建项目 |
| GET | `/workspaces/{wid}/projects` | 列出项目 |
| GET | `/workspaces/{wid}/projects/{pid}` | 项目详情 |
| PATCH | `/workspaces/{wid}/projects/{pid}` | 更新项目 |
| DELETE | `/workspaces/{wid}/projects/{pid}` | 删除项目 |

### Tasks（6）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/workspaces/{wid}/projects/{pid}/tasks` | 创建任务 |
| GET | `/workspaces/{wid}/tasks` | 列出任务（支持筛选/排序/分页） |
| GET | `/workspaces/{wid}/tasks/{tid}` | 任务详情 |
| PATCH | `/workspaces/{wid}/tasks/{tid}` | 更新任务（乐观锁 `version`） |
| POST | `/workspaces/{wid}/tasks/{tid}/status-transitions` | 状态流转 |
| DELETE | `/workspaces/{wid}/tasks/{tid}` | 删除任务 |

**筛选参数**：`status`, `assignee_id`, `project_id`, `tag`, `due_at_from`, `due_at_to`, `sort_by`, `sort_order`

### Collaboration（8）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST / GET | `.../tasks/{tid}/comments` | 评论 CRUD |
| PATCH / DELETE | `.../comments/{cid}` | |
| POST | `.../tasks/{tid}/tags` | 添加标签 |
| DELETE | `.../tasks/{tid}/tags/{tag}` | 删除标签 |
| POST | `.../tasks/{tid}/watchers` | 添加关注者 |
| DELETE | `.../tasks/{tid}/watchers/{uid}` | 删除关注者 |

### Audit（1）

- `GET /workspaces/{wid}/audit-logs` — 审计日志（分页，需 owner/admin 权限）

## 数据库迁移

```bash
alembic upgrade head     # 升级到最新
alembic downgrade -1     # 回滚一步
```

| 版本 | 说明 |
|------|------|
| `64acdc31bcad` | Phase A：添加协作 schema |
| `75d651717369` | Phase B：todos → tasks 迁移 |
| `921743ddcb91` | Phase C：删除 todos 表 |

## 测试

```bash
pytest -q
```

覆盖：认证、工作空间、项目、任务 CRUD、权限控制、审计日志、迁移检查。

## 环境变量

### 后端 (.env)

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `APP_NAME` | 应用名称 | `Todo API` |
| `DEBUG` | 调试模式 | `true` |
| `DATABASE_URL` | 数据库连接串 | `sqlite+aiosqlite:///./todo.db` |
| `SECRET_KEY` | JWT 密钥 | — |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 过期时间 | `30` |

### 前端 (.env.local)

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `NEXT_PUBLIC_API_URL` | 后端 API 地址 | `http://localhost:8000` |
