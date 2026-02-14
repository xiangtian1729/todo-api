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
    logger = logging.getLogger("todo_api")
    logger.setLevel(logging.INFO)

    # 避免重复添加处理器（应用重载时可能会多次调用）
    if not logger.handlers:
        # 创建控制台输出处理器
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)

        # 设置日志格式：时间 | 级别 | 消息
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# 全局日志实例
logger = setup_logging()
