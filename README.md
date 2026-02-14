# 📝 Todo API

一个使用 Python + FastAPI 构建的专业级待办事项 RESTful API。

## 技术栈

- **Python** 3.13
- **FastAPI** — Web 框架
- **SQLAlchemy** — ORM（异步）
- **SQLite** — 数据库
- **Pydantic** — 数据验证
- **Uvicorn** — ASGI 服务器

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
pip install -r requirements.txt
```

### 4. 配置环境变量

复制示例配置文件并按需修改：

```bash
cp .env.example .env
```

### 5. 启动服务

```bash
cd src
python -m uvicorn app.main:app --reload --port 8000
```

服务启动后访问：
- **API 文档（Swagger UI）**: http://127.0.0.1:8000/docs
- **健康检查**: http://127.0.0.1:8000/health

## API 端点

| 方法 | URL | 功能 | 状态码 |
|------|-----|------|--------|
| `POST` | `/todos/` | 创建待办事项 | 201 |
| `GET` | `/todos/` | 获取待办事项列表 | 200 |
| `GET` | `/todos/{id}` | 获取单个待办事项 | 200 |
| `PATCH` | `/todos/{id}` | 更新待办事项 | 200 |
| `DELETE` | `/todos/{id}` | 删除待办事项 | 204 |

## 项目结构

```
src/app/
├── main.py          # 应用入口
├── config.py        # 配置管理
├── database.py      # 数据库连接
├── models/          # 数据库模型
├── schemas/         # 数据验证模型
└── routers/         # API 路由
```

## 运行测试

```bash
pytest
```

## 许可证

MIT
