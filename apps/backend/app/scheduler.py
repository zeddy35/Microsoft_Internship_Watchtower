"""APScheduler wiring: the periodic refresh and the weekly digest.

Both jobs are registered with `max_instances=1` and `coalesce=True`, which is
the whole overlap story: a refresh that runs long (a big GitHub sync, a slow
local model) simply delays the next tick instead of starting a second pass on
the same DuckDB connection, and a run missed while the process was down fires
once on restart rather than N times.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import Settings
from app.core.db import get_connection
from app.jobs import run_refresh

logger = logging.getLogger(__name__)

REFRESH_JOB_ID = "watchtower-refresh"
DIGEST_JOB_ID = "watchtower-weekly-digest"


async def _refresh_job() -> None:
    result = await run_refresh(get_connection())
    logger.info(
        "Scheduled refresh: %d metric rows, %d teams, %d anomalies open",
        result.metric_rows,
        result.teams,
        result.anomalies_open,
    )


async def _digest_job() -> None:
    from app.notify.teams import send_weekly_digest

    await send_weekly_digest(get_connection())


async def startup_pass() -> None:
    """Rebuild derived state from what is already stored, without network calls.

    Startup should make the dashboard answer correctly straight away, but it
    should not pull GitHub or spin up the local model on every dev reload, so
    this pass is rollup plus detection only.
    """
    try:
        await run_refresh(get_connection(), collect=False, resolve=False, notify=False)
    except Exception:
        logger.exception("Startup pass failed")


def build_scheduler(settings: Settings) -> AsyncIOScheduler:
    """Scheduler with both jobs registered, not yet started."""
    scheduler = AsyncIOScheduler(timezone="UTC")

    scheduler.add_job(
        _refresh_job,
        trigger=IntervalTrigger(minutes=settings.REFRESH_INTERVAL_MINUTES),
        id=REFRESH_JOB_ID,
        name="Collect, roll up, detect, resolve",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )

    scheduler.add_job(
        _digest_job,
        trigger=CronTrigger(
            day_of_week=settings.DIGEST_DAY_OF_WEEK, hour=settings.DIGEST_HOUR, minute=0
        ),
        id=DIGEST_JOB_ID,
        name="Weekly digest to Teams",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )

    return scheduler
