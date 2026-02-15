"""
日志配置模块

为什么需要日志？
    想象你的 API 在服务器上运行，突然有用户反馈"接口报错了"。
    如果没有日志，你只能猜测发生了什么。
    有了日志，你可以清楚地看到：
    - 什么时间收到了什么请求
    - 请求处理了多久
    - 哪里出了错，错误信息是什么

    日志就是应用的"黑匣子"——出了问题时拿来回溯分析。
"""

import logging
import sys
from logging.handlers import RotatingFileHandler

from app.config import settings


class JsonFormatter(logging.Formatter):
    """简单的 JSON 格式化器（生产环境使用，便于日志采集）"""

    def format(self, record: logging.LogRecord) -> str:
        import json

        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging() -> logging.Logger:
    """配置并返回应用日志记录器

    日志级别（从低到高）：
        DEBUG    → 开发调试信息（只在开发时看）
        INFO     → 一般运行信息（请求已处理、服务已启动）
        WARNING  → 警告（不影响运行但需要关注）
        ERROR    → 错误（某个操作失败了）
        CRITICAL → 严重错误（整个应用可能挂了）
    """
    # 创建一个名为 "todo_api" 的日志记录器
    app_logger = logging.getLogger("todo_api")
    app_logger.setLevel(logging.INFO)

    # 避免重复添加处理器（应用重载时可能会多次调用）
    if not app_logger.handlers:
        # 控制台处理器（始终启用）
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)
        app_logger.addHandler(console_handler)

        # 文件处理器（非 DEBUG 模式自动启用，10MB per file，保留 5 份）
        if not settings.DEBUG:
            file_handler = RotatingFileHandler(
                "logs/app.log",
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S"))
            app_logger.addHandler(file_handler)

    return app_logger


# 全局日志实例
logger = setup_logging()
