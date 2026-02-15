"""
应用配置模块

为什么需要这个文件？
    在专业开发中，配置信息（如数据库地址、密钥等）不应该硬编码在代码里，
    而是通过"环境变量"来管理。这样做的好处是：
    1. 安全性：密码等敏感信息不会出现在代码仓库里
    2. 灵活性：开发环境和生产环境可以用不同的配置，无需改代码
    3. 可维护性：所有配置集中管理，方便查找和修改

pydantic-settings 帮我们自动从 .env 文件或系统环境变量中读取配置。
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用全局配置类

    每个属性对应一个环境变量。例如：
    - APP_NAME 对应环境变量 APP_NAME
    - DATABASE_URL 对应环境变量 DATABASE_URL

    默认值用于开发环境，生产环境应通过 .env 文件覆盖。
    """

    # 应用基本信息
    APP_NAME: str = "Todo API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./todo.db"

    # JWT 认证配置
    # SECRET_KEY 用于签名 JWT token（生产环境必须换成随机长字符串！）
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    # Token 过期时间（分钟）
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


# 创建一个全局配置实例，其他模块导入这个实例即可使用配置
# 这是一个常见的设计模式叫"单例"——整个应用只需要一份配置
settings = Settings()
