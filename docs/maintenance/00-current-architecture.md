# 当前架构说明（维护版）

## 文档定位
本文件描述“当前代码真实架构”，用于日常维护、排障和需求迭代评估。  
不是从零教学文档。

建议配合阅读顺序：
1. `src/app/main.py`
2. `src/app/routers/*.py`
3. `src/app/services/*.py`
4. `src/app/database.py` + `src/app/security.py`
5. `migrations/` 与 `tests/`

## 系统概览
- 后端：FastAPI + SQLAlchemy Async + Alembic + SQLite
- 前端：Next.js App Router + TanStack Query + Zustand
- 鉴权：JWT Bearer
- 运行方式：本地开发 / Docker Compose

## 后端分层与职责
| 层 | 目录/文件 | 主要职责 | 不应做的事 |
|---|---|---|---|
| 应用装配层 | `src/app/main.py` | 创建 app、挂中间件、注册路由、全局异常映射 | 写业务规则 |
| 路由层 | `src/app/routers/*.py` | 接收 HTTP 请求、参数校验、依赖注入、调用 service | 复杂业务分支 |
| 业务层 | `src/app/services/*.py` | RBAC、状态机、幂等、并发控制、审计写入 | 直接处理 HTTP 细节 |
| 数据模型层 | `src/app/models/*.py` | ORM 表结构与关系 | 接口入参出参校验 |
| 契约层 | `src/app/schemas/*.py` | Request/Response 数据契约 | 数据库访问 |
| 基础设施层 | `database.py`/`security.py`/`logging_config.py` | DB 会话、安全能力、日志能力 | 业务规则判断 |

## 依赖方向（必须遵守）
- 允许：`routers -> services -> models/database`
- 允许：`routers/services -> schemas`
- 允许：运行时模块读取 `config`
- 禁止：`services -> routers`
- 禁止：`models -> routers/services`

一句话：依赖方向从“外层”指向“内层”，不要反向引用。

## 一次请求的完整路径
```text
Browser
  -> Next.js hooks (TanStack Query)
  -> axios (Bearer token)
  -> FastAPI Router
  -> Service (权限/业务规则)
  -> SQLAlchemy Async Session
  -> SQLite
  -> Response Schema
  -> Browser cache/state update
```

后端内部流程：
1. 进入 `main.py` 注册的中间件（日志、CORS）。
2. 路由函数执行参数校验和依赖注入（`get_db`、`get_current_user`）。
3. 调用 service 执行业务规则。
4. service 读写数据库并提交事务。
5. 路由返回 schema，FastAPI 输出 JSON。

## 数据持久化与迁移
- 运行时数据库访问：`src/app/database.py`
  - `engine`：连接引擎
  - `async_session`：会话工厂
  - `get_db`：依赖注入入口
- 结构迁移：`migrations/`
  - `migrations/env.py`：迁移环境
  - `migrations/versions/*.py`：迁移历史

常用命令：
```bash
alembic current
alembic upgrade head
alembic downgrade -1
```

## 前端运行架构（与后端通信）
- HTTP 客户端：`frontend/src/lib/axios.ts`
  - 从 `NEXT_PUBLIC_API_URL` 读取 API 地址
  - 自动附加 `Authorization: Bearer <token>`
- 服务端状态：TanStack Query
  - provider：`frontend/src/components/providers.tsx`
  - hooks：`frontend/src/hooks/*`
- 本地 UI 状态：Zustand
  - `frontend/src/hooks/use-workspace-store.ts`

## 当前安全基线
- `.env.example` 默认：
  - `APP_ENV=development`
  - `DEBUG=false`
- CORS 来源由 `CORS_ALLOWED_ORIGINS` 显式配置，不再走 DEBUG 通配捷径。
- `APP_ENV=production` 时，默认弱密钥会阻止启动。

## CI 基线
- 后端：`ruff + mypy + pytest`
- 前端：`lint + unit test + build`
- 工作流文件：`.github/workflows/ci.yml`

## 维护时的硬规则
1. 路由层保持薄，业务逻辑沉到 service。
2. 任何模型结构变更必须附带 Alembic 迁移。
3. 新增/修改接口必须更新测试与契约文档。
4. 鉴权/权限逻辑改动必须补至少 1 个反例测试（403/404/409）。
5. 提交前至少执行一次本地质量门禁（lint/type/test/build）。
