"""FastAPI route handlers."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app import __version__
from app.core.config import get_settings
from app.core.exporters import prepare_export
from app.core.jobs import job_manager
from app.db.database import get_db
from app.db.models import JobRecord
from app.models.schemas import (
    HealthResponse,
    JobCreateResponse,
    JobListResponse,
    JobResponse,
    JobStatus,
    ResultResponse,
    ScrapeMode,
    ScrapeRequest,
    SettingsResponse,
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
    }
    if url_required and not request.url:
        raise HTTPException(status_code=422, detail=f"URL is required for {request.mode.value} mode")
    if request.mode == ScrapeMode.SELECTORS and not request.selectors:
        raise HTTPException(status_code=422, detail="At least one CSS selector is required")


@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "error"

    return HealthResponse(status="healthy", version=__version__, database=db_status)


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


@router.get("/jobs", response_model=JobListResponse, tags=["Jobs"])
def list_jobs(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> JobListResponse:
    jobs = job_manager.list_jobs(db, limit=limit)
    return JobListResponse(jobs=[_job_to_response(j) for j in jobs], total=len(jobs))


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
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
