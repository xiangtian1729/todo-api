"""Application settings."""

import logging
import sys

from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_SECRET_KEY = "dev-secret-key-change-in-production"


class Settings(BaseSettings):
    APP_NAME: str = "Todo API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite+aiosqlite:///./todo.db"

    SECRET_KEY: str = _DEFAULT_SECRET_KEY
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Comma-separated origins, e.g. "https://app.example.com,http://localhost:3000"
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]


settings = Settings()

if not settings.DEBUG and settings.SECRET_KEY == _DEFAULT_SECRET_KEY:
    logging.basicConfig(stream=sys.stderr)
    logging.critical(
        "FATAL: SECRET_KEY is using the default value in non-DEBUG mode. "
        "Please set a strong random SECRET_KEY in environment variables.",
    )
    sys.exit(1)
