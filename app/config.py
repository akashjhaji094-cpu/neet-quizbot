"""Application configuration settings."""

import os
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    BOT_TOKEN: str = "MOCK_BOT_TOKEN"
    DATABASE_URL: str = "sqlite:///./quizbot.db"
    BOT_USERNAME: Optional[str] = None
    WEBHOOK_URL: Optional[str] = None
    PORT: int = 8000
    ADMIN_USER_IDS: List[int] = []
    OWNER_USERNAME: Optional[str] = None
    SUPPORT_URL: Optional[str] = None
    DEFAULT_LANGUAGE: str = "en"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str]) -> str:
        if not v:
            return "sqlite:///./quizbot.db"
        # Heroku / older PaaS use postgres://, which SQLAlchemy 1.4/2.0 deprecates
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql://", 1)
        return v

    @field_validator("ADMIN_USER_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            if not v.strip():
                return []
            return [int(x.strip()) for x in v.split(",") if x.strip().isdigit()]
        return v or []


settings = Settings()
