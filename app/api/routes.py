"""FastAPI route handlers."""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app import __version__
from app.core.config import get_settings
from app.core.exporters import prepare_export
from app.core.jobs import get_uptime_seconds, job_manager
from app.core.scraper import AsyncWebScraper, ScraperError
from app.db.database import check_db_connection, get_db
from app.db.models import JobRecord
from app.models.schemas import (
    MAX_PRICE_COMPARE_URLS,
    HealthDetailResponse,
    HealthResponse,
    JobCreateResponse,
    JobListResponse,
    JobResponse,
    JobStatus,
    ModeStats,
    ResultResponse,
    ScrapeMode,
    ScrapeRequest,
    SelectorHintsResponse,
    SettingsResponse,
    StatsResponse,
)

router = APIRouter()


def _job_to_response(job: JobRecord) -> JobResponse:
    return JobResponse(
        id=job.id,
        mode=ScrapeMode(job.mode),
        url=job.url,
        status=JobStatus(job.status),
        progress=job.progress,
        total_items=job.total_items,
        error=job.error,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
        config=job.config or {},
    )


def _validate_request(request: ScrapeRequest) -> None:
    url_required = request.mode in {
        ScrapeMode.META,
        ScrapeMode.LINKS,
        ScrapeMode.TABLES,
        ScrapeMode.SELECTORS,
        ScrapeMode.SITEMAP,
        ScrapeMode.EMAIL_EXTRACT,
        ScrapeMode.JSON_LD,
        ScrapeMode.SOCIAL_META,
        ScrapeMode.READABILITY,
    }
    if url_required and not request.url and not request.urls:
        raise HTTPException(status_code=422, detail=f"URL is required for {request.mode.value} mode")
    if request.mode == ScrapeMode.SELECTORS and not request.selectors:
        raise HTTPException(status_code=422, detail="At least one CSS selector is required")
    if request.mode in (ScrapeMode.PRICE_COMPARE, ScrapeMode.META) and request.urls:
        if len(request.urls) > MAX_PRICE_COMPARE_URLS:
            raise HTTPException(
                status_code=422,
                detail=f"Maximum {MAX_PRICE_COMPARE_URLS} URLs allowed per batch job",
            )
    if request.mode == ScrapeMode.PRICE_COMPARE:
        if not request.urls:
            raise HTTPException(
                status_code=422,
                detail="At least one URL is required for price_compare mode",
            )
        if len(request.urls) > MAX_PRICE_COMPARE_URLS:
            raise HTTPException(
                status_code=422,
                detail=f"Maximum {MAX_PRICE_COMPARE_URLS} URLs allowed per price compare job",
            )


def _compute_stats(db: Session) -> StatsResponse:
    jobs = db.query(JobRecord).all()
    total = len(jobs)
    completed = [j for j in jobs if j.status == JobStatus.COMPLETED.value]
    failed = [j for j in jobs if j.status == JobStatus.FAILED.value]
    finished = completed + failed

    durations: list[float] = []
    for job in finished:
        if job.completed_at and job.created_at:
            delta = (job.completed_at - job.created_at).total_seconds()
            if delta >= 0:
                durations.append(delta)

    avg_duration = round(sum(durations) / len(durations), 2) if durations else None
    success_rate = round(len(completed) / len(finished) * 100, 1) if finished else 0.0

    by_mode: dict[str, list[JobRecord]] = {}
    for job in jobs:
        by_mode.setdefault(job.mode, []).append(job)

    mode_stats: list[ModeStats] = []
    for mode, mode_jobs in sorted(by_mode.items()):
        mode_completed = [j for j in mode_jobs if j.status == JobStatus.COMPLETED.value]
        mode_failed = [j for j in mode_jobs if j.status == JobStatus.FAILED.value]
        mode_finished = mode_completed + mode_failed
        mode_durations = []
        for job in mode_finished:
            if job.completed_at and job.created_at:
                delta = (job.completed_at - job.created_at).total_seconds()
                if delta >= 0:
                    mode_durations.append(delta)
        mode_stats.append(ModeStats(
            mode=mode,
            total=len(mode_jobs),
            completed=len(mode_completed),
            failed=len(mode_failed),
            success_rate=round(
                len(mode_completed) / len(mode_finished) * 100, 1
            ) if mode_finished else 0.0,
            avg_duration_seconds=round(
                sum(mode_durations) / len(mode_durations), 2
            ) if mode_durations else None,
        ))

    return StatsResponse(
        version=__version__,
        total_jobs=total,
        completed_jobs=len(completed),
        failed_jobs=len(failed),
        success_rate=success_rate,
        avg_job_duration_seconds=avg_duration,
        active_jobs=job_manager.active_job_count,
        uptime_seconds=round(get_uptime_seconds(), 1),
        by_mode=mode_stats,
    )


@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check() -> HealthResponse:
    db_status = "connected" if check_db_connection() else "error"
    return HealthResponse(status="healthy" if db_status == "connected" else "degraded", version=__version__, database=db_status)


@router.get("/health/detail", response_model=HealthDetailResponse, tags=["System"])
def health_detail() -> HealthDetailResponse:
    settings = get_settings()
    db_ok = check_db_connection()
    return HealthDetailResponse(
        status="healthy" if db_ok else "degraded",
        version=__version__,
        database="connected" if db_ok else "error",
        uptime_seconds=round(get_uptime_seconds(), 1),
        active_jobs=job_manager.active_job_count,
        max_concurrent_jobs=settings.max_concurrent_jobs,
        environment=settings.environment,
        api_key_required=bool(settings.api_key),
        ssrf_protection=not settings.allow_private_urls,
        rate_limit_per_minute=settings.rate_limit_per_minute,
    )


@router.get("/health/live", tags=["System"])
def health_live() -> dict[str, str]:
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/health/ready", tags=["System"])
def health_ready() -> dict[str, str]:
    db_ok = check_db_connection()
    if not db_ok:
        raise HTTPException(status_code=503, detail="Database not ready")
    return {"status": "ready", "database": "connected"}


@router.get("/stats", response_model=StatsResponse, tags=["System"])
def get_stats(db: Session = Depends(get_db)) -> StatsResponse:
    return _compute_stats(db)


@router.get("/selector-hints", response_model=SelectorHintsResponse, tags=["Scraping"])
async def get_selector_hints(
    url: str = Query(..., min_length=10, description="Page URL to analyze"),
) -> SelectorHintsResponse:
    settings = get_settings()
    scraper = AsyncWebScraper(
        delay=0,
        timeout=settings.default_timeout,
        retries=settings.default_retries,
        check_robots=False,
        allow_private_urls=settings.allow_private_urls,
    )
    try:
        hints = await scraper.suggest_selectors(url)
    except ScraperError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return SelectorHintsResponse(**hints)


@router.post("/jobs/import-csv", response_model=JobCreateResponse, status_code=202, tags=["Jobs"])
async def import_csv_job(
    background_tasks: BackgroundTasks,
    mode: ScrapeMode = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> JobCreateResponse:
    if mode not in (ScrapeMode.PRICE_COMPARE, ScrapeMode.META):
        raise HTTPException(
            status_code=422,
            detail="CSV import supports price_compare and meta modes only",
        )

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded") from exc

    urls: list[str] = []
    reader = csv.reader(io.StringIO(text))
    for row in reader:
        for cell in row:
            cell = cell.strip()
            if cell.lower() in ("url", "urls") or not cell:
                continue
            if cell.startswith(("http://", "https://")):
                urls.append(cell)

    if not urls:
        raise HTTPException(status_code=422, detail="No valid URLs found in CSV file")
    if len(urls) > MAX_PRICE_COMPARE_URLS:
        raise HTTPException(
            status_code=422,
            detail=f"Maximum {MAX_PRICE_COMPARE_URLS} URLs allowed per import",
        )

    request = ScrapeRequest(mode=mode, urls=urls, check_robots=False, delay=0)
    _validate_request(request)
    job = job_manager.create_job_record(db, request)
    background_tasks.add_task(job_manager.enqueue, db, job, request)
    return JobCreateResponse(
        job_id=job.id,
        status=JobStatus.PENDING,
        message=f"CSV import job queued ({len(urls)} URLs, {mode.value})",
    )


@router.get("/settings", response_model=SettingsResponse, tags=["System"])
def get_app_settings() -> SettingsResponse:
    settings = get_settings()
    return SettingsResponse(
        default_delay=settings.default_delay,
        default_timeout=settings.default_timeout,
        default_retries=settings.default_retries,
        default_user_agent=settings.default_user_agent,
        check_robots_txt=settings.check_robots_txt,
        max_concurrent_jobs=settings.max_concurrent_jobs,
        rate_limit_per_minute=settings.rate_limit_per_minute,
        api_key_required=bool(settings.api_key),
    )


@router.post("/jobs", response_model=JobCreateResponse, status_code=202, tags=["Jobs"])
async def create_job(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> JobCreateResponse:
    _validate_request(request)
    job = job_manager.create_job_record(db, request)
    background_tasks.add_task(job_manager.enqueue, db, job, request)
    return JobCreateResponse(
        job_id=job.id,
        status=JobStatus.PENDING,
        message=f"Scrape job queued ({request.mode.value})",
    )


@router.post("/jobs/{job_id}/retry", response_model=JobCreateResponse, status_code=202, tags=["Jobs"])
async def retry_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> JobCreateResponse:
    original = job_manager.get_job(db, job_id)
    if not original:
        raise HTTPException(status_code=404, detail="Job not found")
    if original.status not in (JobStatus.FAILED.value, JobStatus.CANCELLED.value):
        raise HTTPException(
            status_code=409,
            detail=f"Only failed or cancelled jobs can be retried (current: {original.status})",
        )

    request = job_manager.build_request_from_job(original)
    job = job_manager.create_job_record(db, request)
    background_tasks.add_task(job_manager.enqueue, db, job, request)
    return JobCreateResponse(
        job_id=job.id,
        status=JobStatus.PENDING,
        message=f"Retry job queued from {job_id[:8]}",
    )


@router.get("/jobs", response_model=JobListResponse, tags=["Jobs"])
def list_jobs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    mobile: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> JobListResponse:
    effective_limit = min(limit, 10) if mobile else limit
    jobs = job_manager.list_jobs(db, limit=effective_limit, offset=offset)
    total = db.query(JobRecord).count()
    return JobListResponse(jobs=[_job_to_response(j) for j in jobs], total=total)


@router.get("/jobs/{job_id}", response_model=JobResponse, tags=["Jobs"])
def get_job(job_id: str, db: Session = Depends(get_db)) -> JobResponse:
    job = job_manager.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_response(job)


@router.get("/jobs/{job_id}/results", response_model=ResultResponse, tags=["Jobs"])
def get_results(job_id: str, db: Session = Depends(get_db)) -> ResultResponse:
    job = job_manager.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.COMPLETED.value:
        raise HTTPException(status_code=409, detail=f"Job is {job.status}, results not ready")

    result = job_manager.get_result(db, job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Results not found")

    return ResultResponse(job_id=job_id, data=result.data, item_count=result.item_count)


@router.get("/jobs/{job_id}/export", tags=["Jobs"])
def export_results(
    job_id: str,
    format: str = Query(default="json", pattern="^(json|csv|xlsx)$"),
    db: Session = Depends(get_db),
) -> Response:
    job = job_manager.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.COMPLETED.value:
        raise HTTPException(status_code=409, detail=f"Job is {job.status}, export not ready")

    result = job_manager.get_result(db, job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Results not found")

    content, media_type, suffix = prepare_export(result.data, format)
    filename = f"scrape_{job.mode}_{job_id[:8]}.{suffix}"

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )
