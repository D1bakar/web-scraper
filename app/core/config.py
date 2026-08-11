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
    app_version: str = "2.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    database_url: str = "sqlite:///./data/scraper.db"

    default_delay: float = 1.0
    default_timeout: int = 15
    default_retries: int = 3
    default_user_agent: str = (
        "Mozilla/5.0 (compatible; WebScraperPro/2.0; "
        "+https://github.com/D1bakar/web-scraper)"
    )
    max_concurrent_jobs: int = 5
    rate_limit_per_minute: int = 60
    check_robots_txt: bool = True

    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
