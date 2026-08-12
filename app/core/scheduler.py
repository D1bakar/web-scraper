"""Simple interval-based job scheduler."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import timedelta

from app.core.jobs import job_manager
from app.db.database import get_session_factory, safe_commit
from app.db.models import ScheduleRecord, utcnow
from app.models.schemas import ScrapeMode, ScrapeRequest

logger = logging.getLogger(__name__)

_scheduler_task: asyncio.Task | None = None


def _interval_minutes(schedule: ScheduleRecord) -> int:
    if schedule.interval_minutes:
        return max(schedule.interval_minutes, 1)
    mapping = {"hourly": 60, "daily": 1440}
    return mapping.get(schedule.frequency or "hourly", 60)


async def _run_due_schedules() -> None:
    db = get_session_factory()()
    try:
        now = utcnow()
        schedules = (
            db.query(ScheduleRecord)
            .filter(ScheduleRecord.enabled.is_(True))
            .all()
        )
        for sched in schedules:
            interval = _interval_minutes(sched)
            due = sched.next_run is None or sched.next_run <= now
            if not due:
                continue
            try:
                config = sched.config or {}
                allowed = {
                    k: v
                    for k, v in config.items()
                    if k in ScrapeRequest.model_fields and k != "mode"
                }
                request = ScrapeRequest(mode=ScrapeMode(sched.mode), **allowed)
                job = job_manager.create_job_record(db, request)
                await job_manager.enqueue(db, job, request)
                sched.last_run = now
                sched.next_run = now + timedelta(minutes=interval)
                sched.updated_at = now
                safe_commit(db)
                logger.info("Schedule %s triggered job %s", sched.id, job.id)
            except Exception as exc:
                logger.warning("Schedule %s failed: %s", sched.id, exc)
    finally:
        db.close()


async def _scheduler_loop() -> None:
    while True:
        try:
            await _run_due_schedules()
        except Exception as exc:
            logger.warning("Scheduler loop error: %s", exc)
        await asyncio.sleep(60)


def start_scheduler() -> None:
    global _scheduler_task
    if _scheduler_task is None or _scheduler_task.done():
        _scheduler_task = asyncio.create_task(_scheduler_loop())


def stop_scheduler() -> None:
    global _scheduler_task
    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()
    _scheduler_task = None


def create_schedule_record(
    *,
    name: str,
    mode: str,
    config: dict,
    frequency: str = "hourly",
    interval_minutes: int | None = None,
) -> ScheduleRecord:
    now = utcnow()
    interval = interval_minutes or (60 if frequency == "hourly" else 1440)
    return ScheduleRecord(
        id=str(uuid.uuid4()),
        name=name,
        mode=mode,
        config=config,
        frequency=frequency,
        interval_minutes=interval,
        enabled=True,
        last_run=None,
        next_run=now,
        created_at=now,
        updated_at=now,
    )
