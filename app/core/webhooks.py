"""Optional webhook notifications on job completion."""

from __future__ import annotations

import logging

import httpx

from app.db.database import get_session_factory, safe_commit
from app.db.models import WebhookDeliveryLog, WebhookRecord

logger = logging.getLogger(__name__)


async def notify_webhook(
    webhook_url: str,
    *,
    job_id: str,
    status: str,
    mode: str,
    item_count: int = 0,
    error: str | None = None,
    webhook_id: str | None = None,
) -> None:
    event = "job.completed" if status == "completed" else "job.failed"
    payload = {
        "event": event,
        "job_id": job_id,
        "status": status,
        "mode": mode,
        "item_count": item_count,
        "error": error,
    }
    status_code = None
    success = False
    err_msg = None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(webhook_url, json=payload)
            status_code = response.status_code
            response.raise_for_status()
            success = True
        logger.info("Webhook notified for job %s", job_id)
    except Exception as exc:
        err_msg = str(exc)
        logger.warning("Webhook notification failed for job %s: %s", job_id, exc)

    if webhook_id:
        db = get_session_factory()()
        try:
            db.add(
                WebhookDeliveryLog(
                    webhook_id=webhook_id,
                    job_id=job_id,
                    event=event,
                    status_code=status_code,
                    success=success,
                    error=err_msg,
                )
            )
            safe_commit(db)
        finally:
            db.close()


async def dispatch_job_webhooks(
    *,
    job_id: str,
    status: str,
    mode: str,
    item_count: int = 0,
    error: str | None = None,
) -> None:
    from app.core.config import get_settings

    settings = get_settings()
    event = "job.completed" if status == "completed" else "job.failed"

    if settings.webhook_url:
        await notify_webhook(
            settings.webhook_url,
            job_id=job_id,
            status=status,
            mode=mode,
            item_count=item_count,
            error=error,
        )

    db = get_session_factory()()
    try:
        hooks = (
            db.query(WebhookRecord)
            .filter(WebhookRecord.enabled.is_(True))
            .all()
        )
        for hook in hooks:
            if event not in (hook.events or []):
                continue
            await notify_webhook(
                hook.url,
                job_id=job_id,
                status=status,
                mode=mode,
                item_count=item_count,
                error=error,
                webhook_id=hook.id,
            )
    finally:
        db.close()
