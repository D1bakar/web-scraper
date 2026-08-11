"""Pydantic request/response models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator


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
    user_agent: str | None = None
    check_robots: bool | None = None

    @field_validator("selectors")
    @classmethod
    def validate_selectors(cls, v: list[str]) -> list[str]:
        return [s.strip() for s in v if s.strip()]

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, v: list[str]) -> list[str]:
        cleaned = [u.strip() for u in v if u.strip()]
        if len(cleaned) > MAX_PRICE_COMPARE_URLS:
            raise ValueError(f"Maximum {MAX_PRICE_COMPARE_URLS} URLs allowed per price compare job")
        return cleaned

    @field_validator("price_selector", "product_label")
    @classmethod
    def strip_optional_strings(cls, v: str | None) -> str | None:
        if v is None:
            return None
        stripped = v.strip()
        return stripped or None


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


class SettingsResponse(BaseModel):
    default_delay: float
    default_timeout: int
    default_retries: int
    default_user_agent: str
    check_robots_txt: bool
    max_concurrent_jobs: int
