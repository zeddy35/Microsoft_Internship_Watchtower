"""The refresh pipeline and the passes the scheduler runs.

One cycle is: collect -> roll up -> detect -> verify -> resolve -> notify.

The verify pass is the part worth reading twice. Every anomaly the engine
flags is stored as an open event; on the next cycle, anything that is no longer
firing gets closed and written to `resolutions` together with how long it
stayed open and what Watchtower had recommended at the time. That table is a
growing set of labeled examples, which is exactly what the predictive layer
needs later - the loop labels its own data instead of waiting for a human to.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime

import duckdb

from app.ai.phi4_client import Phi4Client
from app.ai.resolver import resolve_team
from app.ai.vectorstore import VectorStore
from app.anomaly.engine import Anomaly, detect_team_anomalies
from app.config import get_settings
from app.core.clock import utcnow
from app.core.db import (
    SummaryRow,
    anomaly_event_id,
    clear_anomaly_event,
    get_open_anomaly_events,
    get_summary,
    insert_resolution,
    list_teams,
    upsert_anomaly_event,
    upsert_summary,
)
from app.core.schemas import RefreshResult
from app.metrics.rollup import rollup_metrics

logger = logging.getLogger(__name__)

OUTCOME_CLEARED = "cleared"


@dataclass(frozen=True, slots=True)
class AnomalyPassResult:
    open_count: int
    opened: int
    cleared: int


# --- detect + verify --------------------------------------------------------


def _recommended_action(conn: duckdb.DuckDBPyConnection, team: str) -> str:
    """What Watchtower had advised for this team when the anomaly was open."""
    summary = get_summary(conn, team)
    if summary is None:
        return ""
    try:
        steps = json.loads(summary.remediation_steps)
    except (TypeError, ValueError):
        return ""
    return str(steps[0]) if steps else ""


def run_anomaly_pass(
    conn: duckdb.DuckDBPyConnection, now: datetime | None = None
) -> AnomalyPassResult:
    """Detect anomalies for every team, then close the ones that have cleared."""
    now = now or utcnow()

    firing: dict[str, Anomaly] = {}
    for team in list_teams(conn):
        for anomaly in detect_team_anomalies(conn, team, now=now):
            firing[anomaly_event_id(anomaly.team, anomaly.metric)] = anomaly

    previously_open = {event.id: event for event in get_open_anomaly_events(conn)}

    opened = 0
    for event_id, anomaly in firing.items():
        if event_id not in previously_open:
            opened += 1
        upsert_anomaly_event(
            conn,
            team=anomaly.team,
            metric=anomaly.metric,
            severity=anomaly.severity.value,
            title=anomaly.title,
            description=anomaly.description,
            observed=anomaly.observed,
            baseline=anomaly.baseline,
            z_score=anomaly.z_score,
            seen_at=now,
        )

    cleared = 0
    for event_id, event in previously_open.items():
        if event_id in firing:
            continue
        clear_anomaly_event(conn, event_id, now)
        insert_resolution(
            conn,
            anomaly_id=event_id,
            team=event.team,
            metric=event.metric,
            severity=event.severity,
            action=_recommended_action(conn, event.team),
            outcome=OUTCOME_CLEARED,
            detected_at=event.detected_at,
            resolved_at=now,
        )
        cleared += 1

    logger.info(
        "Anomaly pass: %d firing (%d new), %d cleared", len(firing), opened, cleared
    )
    return AnomalyPassResult(open_count=len(firing), opened=opened, cleared=cleared)


# --- resolver ---------------------------------------------------------------


def run_resolver_pass(
    conn: duckdb.DuckDBPyConnection,
    *,
    client: Phi4Client | None = None,
    store: VectorStore | None = None,
    now: datetime | None = None,
) -> int:
    """Ask Phi-4 for a verdict per team and cache it. Never fatal.

    Local inference is the flakiest dependency in the stack (the endpoint may
    simply not be running), so a failure here degrades the summary card rather
    than the whole refresh.
    """
    now = now or utcnow()
    settings = get_settings()
    written = 0

    for team in list_teams(conn):
        anomalies = detect_team_anomalies(conn, team, now=now)
        try:
            resolution = resolve_team(
                conn,
                team,
                anomalies,
                sprint_goal=settings.SPRINT_GOAL or None,
                client=client,
                store=store,
            )
        except Exception:
            logger.exception("Resolver failed for %s", team)
            continue

        upsert_summary(
            conn,
            SummaryRow(
                team=team,
                summary=resolution.summary,
                root_cause=resolution.root_cause,
                remediation_steps=json.dumps(resolution.remediation_steps),
                verify_signal=resolution.verify_signal,
                on_goal_score=resolution.on_goal_score,
                generated_at=now,
            ),
        )
        written += 1

    return written


# --- full refresh -----------------------------------------------------------


async def run_refresh(
    conn: duckdb.DuckDBPyConnection,
    *,
    collect: bool = True,
    resolve: bool = True,
    notify: bool = True,
) -> RefreshResult:
    """One full cycle. Safe to call from a route or from the scheduler."""
    collected = False
    if collect:
        from app.collectors.github import collect_all

        try:
            await collect_all()
            collected = True
        except Exception:
            logger.exception("Collection failed; continuing with stored data")

    rollup = await asyncio.to_thread(rollup_metrics, conn)
    anomaly_result = await asyncio.to_thread(run_anomaly_pass, conn)

    summaries_written = 0
    if resolve:
        summaries_written = await asyncio.to_thread(run_resolver_pass, conn)

    if notify:
        from app.notify.teams import notify_critical_anomalies

        try:
            await notify_critical_anomalies(conn)
        except Exception:
            logger.exception("Teams notification failed")

    return RefreshResult(
        collected=collected,
        metric_rows=rollup.rows_written,
        teams=rollup.teams,
        anomalies_open=anomaly_result.open_count,
        resolutions_written=anomaly_result.cleared,
        summaries_written=summaries_written,
    )
