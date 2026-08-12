"""Pydantic request/response models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

from app.core.config import get_settings
from app.core.security import (
    SecurityError,
    validate_css_selector,
    validate_selectors,
    validate_url_ssrf,
    validate_urls_list,
)


class ScrapeMode(str, Enum):
    PRICE_COMPARE = "price_compare"
    QUOTES = "quotes"
    META = "meta"
    LINKS = "links"
    TABLES = "tables"
    SELECTORS = "selectors"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


MAX_PRICE_COMPARE_URLS = 50


class ScrapeRequest(BaseModel):
    mode: ScrapeMode
    url: HttpUrl | None = None
    urls: list[str] = Field(default_factory=list)
    selectors: list[str] = Field(default_factory=list)
    price_selector: str | None = None
    product_label: str | None = None
    max_pages: int | None = Field(default=None, ge=1, le=100)
    same_domain: bool = True
    delay: float | None = Field(default=None, ge=0, le=30)
    timeout: int | None = Field(default=None, ge=5, le=120)
    retries: int | None = Field(default=None, ge=1, le=10)
    user_agent: str | None = Field(default=None, max_length=512)
    check_robots: bool | None = None

    @field_validator("selectors")
    @classmethod
    def validate_selectors_field(cls, v: list[str]) -> list[str]:
        stripped = [s.strip() for s in v if s.strip()]
        try:
            return validate_selectors(stripped)
        except SecurityError as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("urls")
    @classmethod
    def validate_urls_field(cls, v: list[str]) -> list[str]:
        cleaned = [u.strip() for u in v if u.strip()]
        if len(cleaned) > MAX_PRICE_COMPARE_URLS:
            raise ValueError(f"Maximum {MAX_PRICE_COMPARE_URLS} URLs allowed per price compare job")
        return cleaned

    @field_validator("price_selector")
    @classmethod
    def validate_price_selector_field(cls, v: str | None) -> str | None:
        if v is None:
            return None
        stripped = v.strip()
        if not stripped:
            return None
        try:
            return validate_css_selector(stripped)
        except SecurityError as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("product_label")
    @classmethod
    def strip_optional_strings(cls, v: str | None) -> str | None:
        if v is None:
            return None
        stripped = v.strip()
        return stripped[:256] if stripped else None

    @model_validator(mode="after")
    def validate_urls_ssrf(self) -> ScrapeRequest:
        settings = get_settings()
        allow_private = settings.allow_private_urls

        if self.url:
            try:
                validate_url_ssrf(str(self.url), allow_private=allow_private)
            except SecurityError as exc:
                raise ValueError(str(exc)) from exc

        if self.urls:
            try:
                self.urls = validate_urls_list(self.urls, allow_private=allow_private)
            except SecurityError as exc:
                raise ValueError(str(exc)) from exc

        return self


class JobCreateResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str


class JobResponse(BaseModel):
    id: str
    mode: ScrapeMode
    url: str | None
    status: JobStatus
    progress: int = 0
    total_items: int = 0
    error: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    config: dict[str, Any] = Field(default_factory=dict)


class JobListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int


class ResultResponse(BaseModel):
    job_id: str
    data: Any
    item_count: int


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str


class HealthDetailResponse(BaseModel):
    status: str
    version: str
    database: str
    uptime_seconds: float
    active_jobs: int
    max_concurrent_jobs: int
    environment: str
    api_key_required: bool
    ssrf_protection: bool
    rate_limit_per_minute: int


class SettingsResponse(BaseModel):
    default_delay: float
    default_timeout: int
    default_retries: int
    default_user_agent: str
    check_robots_txt: bool
    max_concurrent_jobs: int
    rate_limit_per_minute: int
    api_key_required: bool
