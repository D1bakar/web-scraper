"""Application configuration from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Web Scraper Pro"
    app_version: str = "2.6.1"
    environment: str = "development"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    database_url: str = "sqlite:///./data/scraper.db"

    default_delay: float = 1.0
    default_timeout: int = 15
    default_retries: int = 3
    default_user_agent: str = (
        "Mozilla/5.0 (compatible; WebScraperPro/2.6.1; "
        "+https://github.com/D1bakar/web-scraper)"
    )
    max_concurrent_jobs: int = 5
    rate_limit_per_minute: int = 120
    check_robots_txt: bool = True
    allow_private_urls: bool = False

    # Security
    api_key: str | None = None
    admin_user: str | None = None
    admin_password: str | None = None
    session_secret: str | None = None
    cors_origins: str = "*"
    max_request_body_bytes: int = 1_048_576

    # Optional webhook on job complete/fail
    webhook_url: str | None = None

    log_level: str = "INFO"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in ("production", "prod")

    def get_cors_origins(self) -> list[str]:
        if self.is_production and self.cors_origins != "*":
            return [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        if self.cors_origins == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
