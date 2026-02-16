# 运维与排障手册（本地 + Docker）

## 目标
提供一份“可以照抄执行”的运维手册，覆盖本地启动、质量校验、常见故障处理和发布前检查。

## 适用范围
- 开发机环境（Windows 为主）
- 本地联调（前后端分离）
- Docker Compose 一键运行

## 一、本地开发启动

### 1. 后端启动
```powershell
pip install -r requirements-dev.txt
alembic upgrade head
python -m uvicorn app.main:app --app-dir src --reload --port 8000
```

检查点：
- `http://localhost:8000/health`
- `http://localhost:8000/docs`

### 2. 前端启动
```powershell
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

检查点：
- `http://localhost:3000`

## 二、质量门禁命令

### 后端
```powershell
python -m ruff check .
python -m mypy
pytest -q
```

### 前端
```powershell
cd frontend
npm run lint
npm run test
npm run build
```

## 三、Docker Compose 操作

### 启动全栈
```powershell
docker compose up --build
```

### 后台启动
```powershell
docker compose up --build -d
```

### 停止
```powershell
docker compose down
```

### 停止并清空数据卷
```powershell
docker compose down -v
```

## 四、常见故障与处理

### 故障 1：Docker pipe 不存在（Windows）
症状：
- `open //./pipe/docker_engine: The system cannot find the file specified`

处理步骤：
1. 启动 Docker Desktop，确认引擎为 running。
2. 必要时使用管理员 PowerShell。
3. 执行：
```powershell
docker version
docker info
docker context ls
```
4. 若仍失败，检查 WSL 是否安装并重启 Docker Desktop。

### 故障 2：前端连不上后端（网络/CORS/地址）
症状：
- 浏览器报 network error
- 请求打到错误地址
- CORS 报错

处理步骤：
1. 检查前端地址：
```text
frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```
2. 检查后端 CORS：
```text
.env
CORS_ALLOWED_ORIGINS=http://localhost:3000
```
3. 修改后重启前后端进程。

### 故障 3：数据库结构不匹配
症状：
- 缺表/缺字段错误

处理步骤：
```powershell
alembic current
alembic upgrade head
```
若测试库异常，直接重新跑 `pytest -q` 触发重建流程。

### 故障 4：登录后仍持续 401
排查顺序：
1. 登录接口是否返回 `access_token`
2. 请求头是否带 `Authorization: Bearer <token>`
3. 当前后端进程 `SECRET_KEY` 是否与签发 token 时一致
4. token 是否已过期

## 五、环境变量基线
`.env.example` 当前默认值：
- `APP_ENV=development`
- `DEBUG=false`
- `DATABASE_URL=sqlite+aiosqlite:///./todo.db`
- `CORS_ALLOWED_ORIGINS=http://localhost:3000`

生产最低要求：
1. 设置强随机 `SECRET_KEY`
2. 明确配置 `CORS_ALLOWED_ORIGINS`
3. 设置 `APP_ENV=production`

## 六、日志与产物管理
- 运行日志目录：`run-logs/`（已被 `.gitignore` 忽略）
- 不要提交本地 `.env`
- 提交前执行 `git status`，确认无运行时垃圾文件

## 七、发布前最小检查清单
1. 后端通过：`ruff + mypy + pytest`
2. 前端通过：`lint + unit test + build`
3. 涉及 API 变化时更新 `docs/maintenance/10-api-contract.md`
4. 推送后观察 CI 后端和前端 job 全绿

## 八、建议的故障响应顺序
当出现“前端页面不可用”时，按以下顺序最快：
1. 先看端口：`3000/8000` 是否在监听
2. 再看 `/health` 是否 200
3. 再看前端 API 地址和后端 CORS 配置
4. 最后看迁移版本和 token 状态
