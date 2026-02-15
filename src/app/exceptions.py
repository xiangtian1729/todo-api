"""
自定义业务异常

将 Service 层与 HTTP 协议解耦。Service 层抛出业务异常，
由 FastAPI 异常处理器统一转换为 HTTP 响应。
"""


class AppError(Exception):
    """所有业务异常的基类"""

    def __init__(self, detail: str = "An error occurred") -> None:
        self.detail = detail
        super().__init__(detail)


class NotFoundError(AppError):
    """资源未找到（对应 HTTP 404）"""


class ForbiddenError(AppError):
    """权限不足（对应 HTTP 403）"""


class ConflictError(AppError):
    """资源冲突（对应 HTTP 409）"""


class BadRequestError(AppError):
    """请求参数无效（对应 HTTP 400）"""
