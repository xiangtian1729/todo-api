import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine
from app.exceptions import (
    AppError,
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.logging_config import logger
from app.routers import audit as audit_router
from app.routers import auth as auth_router
from app.routers import collaboration as collaboration_router
from app.routers import projects as projects_router
from app.routers import tasks as tasks_router
from app.routers import workspaces as workspaces_router

_EXCEPTION_STATUS_MAP: dict[type[AppError], int] = {
    NotFoundError: 404,
    ForbiddenError: 403,
    ConflictError: 409,
    BadRequestError: 400,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application started | %s v%s", settings.APP_NAME, settings.APP_VERSION)
    yield
    logger.info("Application shutting down...")
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Todo API with team collaboration support.",
    lifespan=lifespan,
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    status_code = _EXCEPTION_STATUS_MAP.get(type(exc), 500)
    return JSONResponse(status_code=status_code, content={"detail": exc.detail})


cors_allowed_origins = settings.cors_allowed_origins
allow_credentials = "*" not in cors_allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    logger.info(
        "%s %s -> %d (%.1fms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


app.include_router(auth_router.router)
app.include_router(workspaces_router.router)
app.include_router(projects_router.router)
app.include_router(tasks_router.router)
app.include_router(collaboration_router.router)
app.include_router(audit_router.router)


@app.get("/health", tags=["System"], summary="Health check")
async def health_check() -> dict:
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
