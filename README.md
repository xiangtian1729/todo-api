# 📝 Todo API

一个使用 Python + FastAPI 构建的待办事项 RESTful API，包含：
- JWT 用户认证
- 用户级 Todo 数据隔离
- Alembic 数据库迁移
- 自动化测试与 CI

## 技术栈

- Python 3.13
- FastAPI
- SQLAlchemy (Async)
- SQLite
- Pydantic
- Alembic
- Uvicorn

## 快速开始

### 1. 克隆项目

```bash
git clone <仓库地址>
cd todo-api
```

### 2. 创建虚拟环境

```bash
# Windows
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1

# macOS / Linux
python3.13 -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
# 本地开发/测试（推荐）
pip install -r requirements-dev.txt

# 仅运行服务（最小运行时依赖）
# pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
```

### 5. 执行数据库迁移

```bash
alembic upgrade head
```

### 6. 启动服务

```bash
python -m uvicorn app.main:app --app-dir src --reload --port 8000
```

服务启动后访问：
- API 文档（Swagger UI）: http://127.0.0.1:8000/docs
- 健康检查: http://127.0.0.1:8000/health

## 认证流程

1. 注册：`POST /auth/register`
2. 登录：`POST /auth/login`（返回 `access_token`）
3. 访问 Todo 接口时，在请求头加：
   - `Authorization: Bearer <access_token>`

> `GET/POST/PATCH/DELETE /todos/*` 均需要 JWT。

## API 端点

| 方法 | URL | 功能 | 鉴权 | 状态码 |
|------|-----|------|------|--------|
| `POST` | `/auth/register` | 用户注册 | 否 | 201 / 409 |
| `POST` | `/auth/login` | 用户登录 | 否 | 200 / 401 |
| `POST` | `/todos/` | 创建待办事项 | 是 | 201 |
| `GET` | `/todos/` | 获取当前用户待办列表 | 是 | 200 |
| `GET` | `/todos/{id}` | 获取单个待办事项 | 是 | 200 / 404 |
| `PATCH` | `/todos/{id}` | 更新待办事项 | 是 | 200 / 404 |
| `DELETE` | `/todos/{id}` | 删除待办事项 | 是 | 204 / 404 |
| `GET` | `/health` | 服务健康检查 | 否 | 200 |

## 数据库迁移

```bash
# 生成新迁移（修改模型后执行）
alembic revision --autogenerate -m "your message"

# 应用迁移
alembic upgrade head

# 回滚一步
alembic downgrade -1
```

如果你本地已有旧版 `todo.db`（由历史 `create_all` 自动建表产生），建议先备份后删除再迁移；  
若你确认表结构与初始迁移一致，也可执行 `alembic stamp head` 对齐版本号。

## Docker

```bash
docker compose up --build -d
docker compose logs -f
docker compose down
```

容器启动时会先执行 `alembic upgrade head`，再启动 API。

## 运行测试

```bash
pytest -q
```

## 项目结构

```text
.
├── src/app/                  # 应用代码
├── tests/                    # 测试代码
├── docs/                     # 学习指南
├── migrations/               # Alembic 迁移脚本
├── alembic.ini               # Alembic 配置
├── requirements.txt          # 运行时依赖
├── requirements-dev.txt      # 开发/测试依赖
├── docker-compose.yml
├── Dockerfile
└── .github/workflows/ci.yml  # CI
```

## 许可证

MIT，见 `LICENSE`。
