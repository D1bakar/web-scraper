"""Optional webhook notifications on job completion."""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)


async def notify_webhook(
    webhook_url: str,
    *,
    job_id: str,
    status: str,
    mode: str,
    item_count: int = 0,
    error: str | None = None,
) -> None:
    payload = {
        "event": "job.completed" if status == "completed" else "job.failed",
        "job_id": job_id,
        "status": status,
        "mode": mode,
        "item_count": item_count,
        "error": error,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
        logger.info("Webhook notified for job %s", job_id)
    except Exception as exc:
        logger.warning("Webhook notification failed for job %s: %s", job_id, exc)
