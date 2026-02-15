# ==========================================
# Todo API Dockerfile
# ==========================================
# Docker 是什么？
#   把你的应用和所有依赖"打包"进一个"容器"里。
#   就像把整个厨房（Python + 依赖 + 代码）放进一个集装箱，
#   运到任何一台服务器上都能直接开始做菜，不用重新装修。
#
# 构建镜像: docker build -t todo-api .
# 运行容器: docker run -p 8000:8000 todo-api
# ==========================================

# ---------- 第 1 步：选择基础镜像 ----------
# python:3.13-slim 是官方 Python 精简版镜像，体积小、安全
FROM python:3.13-slim

# ---------- 第 2 步：设置工作目录 ----------
# 容器内的 /app 目录就是我们的"项目根目录"
WORKDIR /app
ENV PYTHONPATH=/app/src

# ---------- 第 3 步：先安装依赖（利用 Docker 缓存） ----------
# 为什么先复制 requirements.txt 再装依赖，最后才复制代码？
# 因为 Docker 是分层缓存的：
#   - 如果 requirements.txt 没变，这一层会被缓存，不需要重新 pip install
#   - 只有代码变了才需要重新构建最后一层
#   - 这样每次改代码后重新构建非常快（几秒 vs 几分钟）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- 第 4 步：复制源代码 ----------
COPY src/ ./src/
COPY alembic.ini ./
COPY migrations/ ./migrations/

# ---------- 第 5 步：暴露端口 ----------
# 告诉 Docker "这个容器会在 8000 端口提供服务"
EXPOSE 8000

# ---------- 第 6 步：启动命令 ----------
# 容器启动时执行这个命令
# --host 0.0.0.0 让容器外也能访问（默认是 127.0.0.1 只允许容器内访问）
CMD ["sh", "-c", "alembic upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]
