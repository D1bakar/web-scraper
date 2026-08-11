"""In-memory job queue with SQLite persistence."""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.scraper import AsyncWebScraper, ScraperError
from app.db.models import JobRecord, ResultRecord, utcnow
from app.models.schemas import JobStatus, ScrapeMode, ScrapeRequest

logger = logging.getLogger(__name__)


def _count_items(data: Any) -> int:
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        if "rows" in data:
            return 1
        return 1
    return 1


class JobManager:
    """Manages scrape jobs with async execution and DB persistence."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._semaphore = asyncio.Semaphore(self.settings.max_concurrent_jobs)
        self._running: dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()

    def create_job_record(self, db: Session, request: ScrapeRequest) -> JobRecord:
        job_id = str(uuid.uuid4())
        config = {
            "max_pages": request.max_pages,
            "same_domain": request.same_domain,
            "selectors": request.selectors,
            "delay": request.delay or self.settings.default_delay,
            "timeout": request.timeout or self.settings.default_timeout,
            "retries": request.retries or self.settings.default_retries,
            "user_agent": request.user_agent or self.settings.default_user_agent,
            "check_robots": (
                request.check_robots
                if request.check_robots is not None
                else self.settings.check_robots_txt
            ),
        }

        record = JobRecord(
            id=job_id,
            mode=request.mode.value,
            url=str(request.url) if request.url else None,
            status=JobStatus.PENDING.value,
            config=config,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def get_job(self, db: Session, job_id: str) -> JobRecord | None:
        return db.query(JobRecord).filter(JobRecord.id == job_id).first()

    def list_jobs(self, db: Session, limit: int = 50) -> list[JobRecord]:
        return (
            db.query(JobRecord)
            .order_by(JobRecord.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_result(self, db: Session, job_id: str) -> ResultRecord | None:
        return db.query(ResultRecord).filter(ResultRecord.job_id == job_id).first()

    def _update_job(
        self,
        db: Session,
        job: JobRecord,
        *,
        status: str | None = None,
        progress: int | None = None,
        total_items: int | None = None,
        error: str | None = None,
        completed: bool = False,
    ) -> None:
        if status is not None:
            job.status = status
        if progress is not None:
            job.progress = progress
        if total_items is not None:
            job.total_items = total_items
        if error is not None:
            job.error = error
        job.updated_at = utcnow()
        if completed:
            job.completed_at = utcnow()
        db.commit()

    def _save_result(self, db: Session, job_id: str, data: Any) -> None:
        count = _count_items(data) if isinstance(data, list) else 1
        existing = self.get_result(db, job_id)
        if existing:
            existing.data = data
            existing.item_count = count
        else:
            db.add(ResultRecord(job_id=job_id, data=data, item_count=count))
        db.commit()

    async def enqueue(self, db: Session, job: JobRecord, request: ScrapeRequest) -> None:
        async with self._lock:
            if job.id in self._running:
                return
            task = asyncio.create_task(self._run_job(job.id, request))
            self._running[job.id] = task

    async def _run_job(self, job_id: str, request: ScrapeRequest) -> None:
        from app.db.database import _SessionLocal

        async with self._semaphore:
            db = _SessionLocal()
            try:
                job = self.get_job(db, job_id)
                if not job:
                    return

                self._update_job(db, job, status=JobStatus.RUNNING.value)

                config = job.config or {}
                scraper = AsyncWebScraper(
                    delay=config.get("delay", self.settings.default_delay),
                    timeout=config.get("timeout", self.settings.default_timeout),
                    retries=config.get("retries", self.settings.default_retries),
                    user_agent=config.get("user_agent"),
                    check_robots=config.get("check_robots", True),
                )

                async def on_progress(page: int, items: int) -> None:
                    self._update_job(db, job, progress=page, total_items=items)

                data: Any
                if request.mode == ScrapeMode.QUOTES:
                    data = await scraper.scrape_quotes(
                        max_pages=config.get("max_pages"),
                        progress_callback=on_progress,
                    )
                elif request.mode == ScrapeMode.META:
                    if not request.url:
                        raise ScraperError("URL is required for meta mode")
                    data = await scraper.scrape_page_meta(str(request.url))
                elif request.mode == ScrapeMode.LINKS:
                    if not request.url:
                        raise ScraperError("URL is required for links mode")
                    data = await scraper.scrape_links(
                        str(request.url),
                        same_domain=config.get("same_domain", True),
                    )
                elif request.mode == ScrapeMode.TABLES:
                    if not request.url:
                        raise ScraperError("URL is required for tables mode")
                    data = await scraper.scrape_tables(str(request.url))
                elif request.mode == ScrapeMode.SELECTORS:
                    if not request.url:
                        raise ScraperError("URL is required for selectors mode")
                    selectors = config.get("selectors") or []
                    if not selectors:
                        raise ScraperError("At least one CSS selector is required")
                    data = await scraper.scrape_selectors(str(request.url), selectors)
                else:
                    raise ScraperError(f"Unknown mode: {request.mode}")

                self._save_result(db, job_id, data)
                item_count = len(data) if isinstance(data, list) else 1
                self._update_job(
                    db,
                    job,
                    status=JobStatus.COMPLETED.value,
                    progress=100,
                    total_items=item_count,
                    completed=True,
                )
                logger.info("Job %s completed with %d items", job_id, item_count)

            except ScraperError as exc:
                logger.error("Job %s failed: %s", job_id, exc)
                job = self.get_job(db, job_id)
                if job:
                    self._update_job(
                        db,
                        job,
                        status=JobStatus.FAILED.value,
                        error=str(exc),
                        completed=True,
                    )
            except Exception as exc:
                logger.exception("Job %s unexpected error", job_id)
                job = self.get_job(db, job_id)
                if job:
                    self._update_job(
                        db,
                        job,
                        status=JobStatus.FAILED.value,
                        error=f"Internal error: {exc}",
                        completed=True,
                    )
            finally:
                db.close()
                async with self._lock:
                    self._running.pop(job_id, None)


job_manager = JobManager()
