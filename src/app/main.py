"""
FastAPI 应用入口

这个文件是整个应用的"总指挥"，负责：
    1. 创建 FastAPI 应用实例
    2. 注册所有路由（告诉 FastAPI："这些 URL 归谁管"）
    3. 设置应用启动/关闭时要做的事（比如创建数据库表）

为什么叫 main.py？
    这是 Python 社区的约定俗成。
    运行应用时，uvicorn 会找到这个文件中的 app 对象来启动服务。
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.config import settings
from app.database import engine
from app.logging_config import logger
from app.models.todo import Base
from app.models.user import User  # noqa: F401 — 确保 User 表被 Base 认识
from app.routers import todo as todo_router
from app.routers import auth as auth_router


# ========== 应用生命周期管理 ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    """管理应用的启动和关闭过程

    这个函数在应用启动时执行 yield 之前的代码，
    在应用关闭时执行 yield 之后的代码。

    好比开店和关店：
        开店前：检查设备、准备食材（创建数据库表）
        关店后：清理厨房、关灯（释放数据库连接）
    """
    # --- 启动时 ---
    # 创建所有数据库表（如果不存在）
    # 这行代码会检查 Base 认识的所有模型（目前是 Todo），
    # 如果对应的表不存在，就自动创建
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Application started | %s v%s", settings.APP_NAME, settings.APP_VERSION)

    yield  # 应用运行中...

    # --- 关闭时 ---
    logger.info("Application shutting down...")
    await engine.dispose()


# ========== 创建 FastAPI 应用实例 ==========
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="一个专业的待办事项 API，支持完整的 CRUD 操作。",
    lifespan=lifespan,
)

# ========== 请求日志中间件 ==========
# 中间件（Middleware）就像一个"拦截器"：
# 每个请求进来时先经过它，每个响应出去时也经过它。
# 这里我们用它来记录每个请求的方法、URL、状态码和耗时。
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    logger.info(
        "%s %s → %d (%.1fms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# ========== 注册路由 ==========
app.include_router(auth_router.router)
app.include_router(todo_router.router)


# ========== 健康检查端点 ==========
@app.get(
    "/health",
    tags=["System"],
    summary="健康检查",
    description="检查 API 服务是否正常运行。",
)
async def health_check() -> dict:
    """一个简单的健康检查端点

    运维团队和监控工具会定期访问这个 URL，
    如果返回正常，说明服务还活着。
    这是生产环境的标准做法。
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
