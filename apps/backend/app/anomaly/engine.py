"""Anomaly engine: rolling-baseline z-scores plus rule checks per team.

The engine reads pre-rolled daily metrics from `metrics_daily` (populated by
the metrics rollup) and the raw `pull_requests` table for the stale-PR rule.
For each team it compares the latest observed value of each tracked metric
against the mean+std of a trailing window and flags statistically unusual
*and* directionally bad movements (a commit drop matters, a commit surge does
not). Rules cover the cases a pure z-score would miss or explain poorly:
stale PRs, review-time spikes, commit drops, and push drops.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import StrEnum

import duckdb

from app.core.clock import utcnow
from app.core.db import (
    get_latest_metric,
    get_rolling_baseline,
    get_stale_open_prs,
    list_teams,
)

# --- tracked metrics --------------------------------------------------------

# Metric names shared with the rollup that writes metrics_daily. Keep in sync.
METRIC_COMMITS_PER_DAY = "commits_per_day"
METRIC_PUSHES_PER_DAY = "pushes_per_day"
METRIC_REVIEW_TIME_HOURS = "review_time_hours"


class Direction(StrEnum):
    """Which way a metric has to move to be considered bad."""

    DROP = "drop"  # bad when it falls below baseline (commits, pushes)
    SPIKE = "spike"  # bad when it rises above baseline (review time)


@dataclass(frozen=True, slots=True)
class MetricSpec:
    metric: str
    label: str
    unit: str
    bad_direction: Direction


TRACKED_METRICS: tuple[MetricSpec, ...] = (
    MetricSpec(METRIC_COMMITS_PER_DAY, "Commit volume", "commits/day", Direction.DROP),
    MetricSpec(METRIC_PUSHES_PER_DAY, "Push volume", "pushes/day", Direction.DROP),
    MetricSpec(
        METRIC_REVIEW_TIME_HOURS, "Review time", "hours", Direction.SPIKE
    ),
)

# --- tuning knobs -----------------------------------------------------------

BASELINE_WINDOW_DAYS = 28
MIN_BASELINE_SAMPLES = 5
WARNING_Z = 2.0
CRITICAL_Z = 3.0
STALE_PR_DAYS = 7

# --- output type ------------------------------------------------------------


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class Anomaly:
    """A flagged deviation, shaped to map cleanly onto the frontend schema."""

    team: str
    metric: str
    severity: Severity
    title: str
    description: str
    detected_at: datetime
    observed: float
    baseline: float
    z_score: float


# --- core -------------------------------------------------------------------


def _severity_for_z(abs_z: float) -> Severity | None:
    if abs_z >= CRITICAL_Z:
        return Severity.CRITICAL
    if abs_z >= WARNING_Z:
        return Severity.WARNING
    return None


def _pct_change(observed: float, baseline: float) -> float:
    if baseline == 0:
        return 0.0
    return (observed - baseline) / baseline * 100.0


def evaluate_metric(
    conn: duckdb.DuckDBPyConnection,
    team: str,
    spec: MetricSpec,
    as_of: date,
    now: datetime,
) -> Anomaly | None:
    """Flag a team/metric if its latest value is a bad, statistically unusual move."""
    latest = get_latest_metric(conn, team, spec.metric, as_of)
    if latest is None:
        return None

    baseline = get_rolling_baseline(
        conn, team, spec.metric, latest.day, BASELINE_WINDOW_DAYS
    )
    if baseline is None or baseline.sample_size < MIN_BASELINE_SAMPLES:
        return None
    if baseline.stddev == 0:
        return None

    z = (latest.value - baseline.mean) / baseline.stddev

    # Only care about moves in the metric's bad direction.
    is_bad = (spec.bad_direction is Direction.DROP and z < 0) or (
        spec.bad_direction is Direction.SPIKE and z > 0
    )
    if not is_bad:
        return None

    severity = _severity_for_z(abs(z))
    if severity is None:
        return None

    pct = _pct_change(latest.value, baseline.mean)
    verb = "dropped" if spec.bad_direction is Direction.DROP else "spiked"
    title = f"{spec.label} {verb}"
    description = (
        f"{spec.label} is {latest.value:.1f} {spec.unit}, "
        f"{abs(pct):.0f}% {'below' if pct < 0 else 'above'} the "
        f"{BASELINE_WINDOW_DAYS}-day baseline of {baseline.mean:.1f} {spec.unit} "
        f"(z={z:.1f})."
    )
    return Anomaly(
        team=team,
        metric=spec.metric,
        severity=severity,
        title=title,
        description=description,
        detected_at=now,
        observed=latest.value,
        baseline=baseline.mean,
        z_score=z,
    )


def evaluate_stale_prs(
    conn: duckdb.DuckDBPyConnection, team: str, now: datetime
) -> Anomaly | None:
    """Flag open PRs sitting unreviewed/unmerged past the staleness threshold."""
    stale = get_stale_open_prs(conn, team, now, STALE_PR_DAYS)
    if not stale:
        return None

    oldest = max(stale, key=lambda pr: pr.age_days)
    count = len(stale)
    severity = Severity.CRITICAL if oldest.age_days >= 2 * STALE_PR_DAYS else Severity.WARNING
    noun = "PR" if count == 1 else "PRs"
    title = f"{count} stale {noun}"
    description = (
        f"{count} open {noun} unmerged for more than {STALE_PR_DAYS} days; "
        f"the oldest ({oldest.repo}#{oldest.id}) has been open {oldest.age_days} days."
    )
    return Anomaly(
        team=team,
        metric="stale_prs",
        severity=severity,
        title=title,
        description=description,
        detected_at=now,
        observed=float(count),
        baseline=0.0,
        z_score=0.0,
    )


def detect_team_anomalies(
    conn: duckdb.DuckDBPyConnection,
    team: str,
    as_of: date | None = None,
    now: datetime | None = None,
) -> list[Anomaly]:
    """Run every metric check and rule for one team, worst first."""
    now = now or utcnow()
    as_of = as_of or now.date() + timedelta(days=1)  # inclusive of today

    anomalies: list[Anomaly] = []
    for spec in TRACKED_METRICS:
        found = evaluate_metric(conn, team, spec, as_of, now)
        if found is not None:
            anomalies.append(found)

    stale = evaluate_stale_prs(conn, team, now)
    if stale is not None:
        anomalies.append(stale)

    severity_rank = {Severity.CRITICAL: 0, Severity.WARNING: 1, Severity.INFO: 2}
    anomalies.sort(key=lambda a: (severity_rank[a.severity], -abs(a.z_score)))
    return anomalies


def detect_all_anomalies(
    conn: duckdb.DuckDBPyConnection,
    as_of: date | None = None,
    now: datetime | None = None,
) -> dict[str, list[Anomaly]]:
    """Anomalies for every team that has repos registered, keyed by team."""
    return {
        team: detect_team_anomalies(conn, team, as_of, now)
        for team in list_teams(conn)
    }
