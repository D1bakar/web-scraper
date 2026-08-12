"""Management routes: schedules, webhooks, API keys, dashboard."""

from __future__ import annotations

import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import generate_api_key, hash_api_key, key_prefix
from app.core.jobs import job_manager
from app.core.scheduler import create_schedule_record
from app.db.database import get_db, safe_commit
from app.db.models import ApiKeyRecord, ScheduleRecord, WebhookDeliveryLog, WebhookRecord
from app.models.schemas import (
    ApiKeyCreateResponse,
    ApiKeyResponse,
    DashboardSummaryResponse,
    JobResponse,
    ScheduleCreateRequest,
    ScheduleResponse,
    ScheduleUpdateRequest,
    ScrapeMode,
    WebhookCreateRequest,
    WebhookDeliveryResponse,
    WebhookResponse,
    WebhookTestResponse,
)

router = APIRouter(tags=["Management"])


def _job_brief(job) -> JobResponse:
    from app.api.routes import _job_to_response

    return _job_to_response(job)


@router.get("/dashboard/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(
    mobile: bool = False,
    db: Session = Depends(get_db),
) -> DashboardSummaryResponse:
    from app.api.routes import _compute_stats

    limit = 5 if mobile else 10
    recent = job_manager.list_jobs(db, limit=limit, offset=0)
    active = [j for j in recent if j.status in ("pending", "running")]
    stats = _compute_stats(db)
    return DashboardSummaryResponse(
        active_jobs=stats.active_jobs,
        total_jobs=stats.total_jobs,
        success_rate=stats.success_rate,
        recent_jobs=[_job_brief(j) for j in recent],
        active_job_list=[_job_brief(j) for j in active],
    )


# --- API Keys ---


@router.get("/api-keys", response_model=list[ApiKeyResponse])
def list_api_keys(db: Session = Depends(get_db)) -> list[ApiKeyResponse]:
    keys = (
        db.query(ApiKeyRecord)
        .filter(ApiKeyRecord.revoked_at.is_(None))
        .order_by(ApiKeyRecord.created_at.desc())
        .all()
    )
    return [
        ApiKeyResponse(
            id=k.id,
            name=k.name,
            key_prefix=k.key_prefix,
            created_at=k.created_at,
        )
        for k in keys
    ]


@router.post("/api-keys", response_model=ApiKeyCreateResponse, status_code=201)
def create_api_key(
    name: str = "Default",
    db: Session = Depends(get_db),
) -> ApiKeyCreateResponse:
    raw = generate_api_key()
    record = ApiKeyRecord(
        id=str(uuid.uuid4()),
        name=name[:128],
        key_hash=hash_api_key(raw),
        key_prefix=key_prefix(raw),
    )
    db.add(record)
    safe_commit(db)
    db.refresh(record)
    return ApiKeyCreateResponse(
        id=record.id,
        name=record.name,
        key_prefix=record.key_prefix,
        created_at=record.created_at,
        api_key=raw,
    )


@router.delete("/api-keys/{key_id}", status_code=204)
def revoke_api_key(key_id: str, db: Session = Depends(get_db)) -> None:
    record = db.query(ApiKeyRecord).filter(ApiKeyRecord.id == key_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="API key not found")
    from app.db.models import utcnow

    record.revoked_at = utcnow()
    safe_commit(db)


# --- Schedules ---


@router.get("/schedules", response_model=list[ScheduleResponse])
def list_schedules(db: Session = Depends(get_db)) -> list[ScheduleResponse]:
    rows = db.query(ScheduleRecord).order_by(ScheduleRecord.created_at.desc()).all()
    return [ScheduleResponse.model_validate(r) for r in rows]


@router.post("/schedules", response_model=ScheduleResponse, status_code=201)
def create_schedule(
    body: ScheduleCreateRequest,
    db: Session = Depends(get_db),
) -> ScheduleResponse:
    if body.mode == ScrapeMode.PRICE_COMPARE and not body.config.get("urls"):
        raise HTTPException(status_code=422, detail="price_compare schedules require urls in config")
    record = create_schedule_record(
        name=body.name,
        mode=body.mode.value,
        config=body.config,
        frequency=body.frequency,
        interval_minutes=body.interval_minutes,
    )
    db.add(record)
    safe_commit(db)
    db.refresh(record)
    return ScheduleResponse.model_validate(record)


@router.patch("/schedules/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    schedule_id: str,
    body: ScheduleUpdateRequest,
    db: Session = Depends(get_db),
) -> ScheduleResponse:
    record = db.query(ScheduleRecord).filter(ScheduleRecord.id == schedule_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Schedule not found")
    if body.name is not None:
        record.name = body.name
    if body.enabled is not None:
        record.enabled = body.enabled
    if body.frequency is not None:
        record.frequency = body.frequency
    if body.interval_minutes is not None:
        record.interval_minutes = body.interval_minutes
    if body.config is not None:
        record.config = body.config
    safe_commit(db)
    db.refresh(record)
    return ScheduleResponse.model_validate(record)


@router.delete("/schedules/{schedule_id}", status_code=204)
def delete_schedule(schedule_id: str, db: Session = Depends(get_db)) -> None:
    record = db.query(ScheduleRecord).filter(ScheduleRecord.id == schedule_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.delete(record)
    safe_commit(db)


# --- Webhooks ---


@router.get("/webhooks", response_model=list[WebhookResponse])
def list_webhooks(db: Session = Depends(get_db)) -> list[WebhookResponse]:
    rows = db.query(WebhookRecord).order_by(WebhookRecord.created_at.desc()).all()
    return [WebhookResponse.model_validate(r) for r in rows]


@router.post("/webhooks", response_model=WebhookResponse, status_code=201)
def create_webhook(
    body: WebhookCreateRequest,
    db: Session = Depends(get_db),
) -> WebhookResponse:
    record = WebhookRecord(
        id=str(uuid.uuid4()),
        name=body.name,
        url=str(body.url),
        events=body.events,
        enabled=body.enabled,
    )
    db.add(record)
    safe_commit(db)
    db.refresh(record)
    return WebhookResponse.model_validate(record)


@router.delete("/webhooks/{webhook_id}", status_code=204)
def delete_webhook(webhook_id: str, db: Session = Depends(get_db)) -> None:
    record = db.query(WebhookRecord).filter(WebhookRecord.id == webhook_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Webhook not found")
    db.delete(record)
    safe_commit(db)


@router.post("/webhooks/{webhook_id}/test", response_model=WebhookTestResponse)
async def test_webhook(webhook_id: str, db: Session = Depends(get_db)) -> WebhookTestResponse:
    record = db.query(WebhookRecord).filter(WebhookRecord.id == webhook_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Webhook not found")
    payload = {
        "event": "webhook.test",
        "message": "Test delivery from Web Scraper Pro",
        "webhook_id": webhook_id,
    }
    status_code = None
    error = None
    success = False
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(record.url, json=payload)
            status_code = response.status_code
            response.raise_for_status()
            success = True
    except Exception as exc:
        error = str(exc)
    log = WebhookDeliveryLog(
        webhook_id=webhook_id,
        job_id=None,
        event="webhook.test",
        status_code=status_code,
        success=success,
        error=error,
    )
    db.add(log)
    safe_commit(db)
    return WebhookTestResponse(success=success, status_code=status_code, error=error)


@router.get("/webhooks/{webhook_id}/deliveries", response_model=list[WebhookDeliveryResponse])
def webhook_deliveries(
    webhook_id: str,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> list[WebhookDeliveryResponse]:
    rows = (
        db.query(WebhookDeliveryLog)
        .filter(WebhookDeliveryLog.webhook_id == webhook_id)
        .order_by(WebhookDeliveryLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [WebhookDeliveryResponse.model_validate(r) for r in rows]
