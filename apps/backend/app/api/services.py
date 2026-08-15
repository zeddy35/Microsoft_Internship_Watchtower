"""Presenters: turn DuckDB rows and engine output into API response models.

The routes stay thin; every judgement call about how raw activity becomes a
number on a card lives here, in one place, documented. Nothing in this module
calls the language model — the Phi-4 verdict is written by the scheduled
resolver pass and read back from the `summaries` table, so a page load never
waits on local inference.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import duckdb

from app.anomaly.bus_factor import compute_team_bus_factor
from app.anomaly.engine import (
    BASELINE_WINDOW_DAYS,
    METRIC_COMMITS_PER_DAY,
    METRIC_PUSHES_PER_DAY,
    METRIC_REVIEW_TIME_HOURS,
)
from app.core.clock import utcnow
from app.core.db import (
    AnomalyEventRow,
    MemberStatsRow,
    get_member_stats,
    get_metric_series,
    get_open_anomaly_events,
    get_rolling_baseline,
    get_summary,
    get_team_repos,
    list_teams,
)
from app.core.schemas import (
    AnomalyOut,
    AnomalySeverity,
    BusFactorAreaOut,
    MemberActivityStatus,
    MetricDirection,
    MetricOut,
    MetricTrend,
    ReviewTimePointOut,
    TeamMemberOut,
    TeamMetricsOut,
    TeamOut,
    TeamStatus,
    TeamSummaryOut,
)

MEMBER_WINDOW_DAYS = 28
REVIEW_HISTORY_DAYS = 30
SPARKLINE_DAYS = 14
HOURS_PER_DAY = 24.0
DAYS_PER_WEEK = 7.0

# Health score: every open anomaly costs points against a perfect 100.
SEVERITY_PENALTY: dict[str, float] = {"critical": 25.0, "warning": 10.0, "info": 3.0}
CRITICAL_SCORE_BELOW = 50.0
AT_RISK_SCORE_BELOW = 75.0

# A metric has to move this far off baseline before the card turns amber/red.
CAUTION_DELTA_PERCENT = 15.0
BAD_DELTA_PERCENT = 40.0

ACTIVE_WITHIN_DAYS = 7
AWAY_WITHIN_DAYS = 21


def slugify(value: str) -> str:
    """Lowercase, hyphenated id safe to use in a URL and as a React key."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "unknown"


# --- team members -----------------------------------------------------------


def _initials(login: str) -> str:
    parts = [p for p in re.split(r"[^A-Za-z0-9]+", login) if p]
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    cleaned = parts[0] if parts else login
    return (cleaned[:2] or "??").upper()


def _activity_status(last_committed_at: datetime, now: datetime) -> MemberActivityStatus:
    age = (now - last_committed_at).days
    if age <= ACTIVE_WITHIN_DAYS:
        return "active"
    if age <= AWAY_WITHIN_DAYS:
        return "away"
    return "offline"


def _member_out(
    row: MemberStatsRow, *, now: datetime, window_days: int, owned_areas: set[str]
) -> TeamMemberOut:
    weeks = max(window_days / DAYS_PER_WEEK, 1.0)
    on_goal = (
        row.linked_commit_count / row.commit_count * 100.0 if row.commit_count else 0.0
    )
    return TeamMemberOut(
        id=slugify(row.author),
        name=row.author,
        role="Area owner" if row.author in owned_areas else "Contributor",
        initials=_initials(row.author),
        commits_per_week=round(row.commit_count / weeks, 1),
        avg_review_time_days=round((row.avg_review_hours or 0.0) / HOURS_PER_DAY, 1),
        on_goal_rate=round(min(on_goal, 100.0), 1),
        activity_status=_activity_status(row.last_committed_at, now),
    )


# --- team ------------------------------------------------------------------


def _health_score(events: list[AnomalyEventRow]) -> float:
    penalty = sum(SEVERITY_PENALTY.get(event.severity, 0.0) for event in events)
    return round(max(0.0, 100.0 - penalty), 0)


def _status_for_score(score: float) -> TeamStatus:
    if score < CRITICAL_SCORE_BELOW:
        return "critical"
    if score < AT_RISK_SCORE_BELOW:
        return "at-risk"
    return "healthy"


def build_team(
    conn: duckdb.DuckDBPyConnection, team: str, now: datetime | None = None
) -> TeamOut:
    """Everything the overview card and the drill-down header need."""
    now = now or utcnow()
    since = now - timedelta(days=MEMBER_WINDOW_DAYS)

    areas = compute_team_bus_factor(conn, team, now=now)
    owned_areas = {area.top_owner for area in areas}
    members = [
        _member_out(
            row, now=now, window_days=MEMBER_WINDOW_DAYS, owned_areas=owned_areas
        )
        for row in get_member_stats(conn, team, since)
    ]

    events = get_open_anomaly_events(conn, team)
    score = _health_score(events)
    repos = get_team_repos(conn, team)
    activity = [
        row.value
        for row in get_metric_series(
            conn,
            team,
            METRIC_COMMITS_PER_DAY,
            now.date() - timedelta(days=SPARKLINE_DAYS - 1),
            now.date() + timedelta(days=1),
        )
    ]

    return TeamOut(
        id=slugify(team),
        name=team,
        status=_status_for_score(score),
        health_score=score,
        engineer_count=len(members),
        source=", ".join(repos) if repos else "GitHub",
        members=members,
        bus_factor_areas=[
            BusFactorAreaOut(
                id=slugify(area.area),
                area=area.area,
                top_owner=area.top_owner,
                ownership_percent=area.ownership_percent,
                risk_level=area.risk_level.value,
            )
            for area in areas
        ],
        activity=activity,
    )


def list_team_names(conn: duckdb.DuckDBPyConnection) -> list[str]:
    return list_teams(conn)


def resolve_team_name(conn: duckdb.DuckDBPyConnection, team_id: str) -> str | None:
    """Map a URL slug back to the stored team name."""
    for team in list_teams(conn):
        if slugify(team) == team_id or team == team_id:
            return team
    return None


def build_teams(
    conn: duckdb.DuckDBPyConnection, now: datetime | None = None
) -> list[TeamOut]:
    """Every team, worst health first, so the overview needs no client sort."""
    teams = [build_team(conn, team, now) for team in list_teams(conn)]
    teams.sort(key=lambda t: t.health_score)
    return teams


# --- metrics ----------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _MetricView:
    """How one stored metric is presented on a KPI card."""

    id: str
    metric: str
    label: str
    unit: str
    scale: float  # stored unit -> display unit
    bad_when_up: bool


_METRIC_VIEWS: tuple[_MetricView, ...] = (
    _MetricView(
        "commit-activity",
        METRIC_COMMITS_PER_DAY,
        "Commit activity",
        "/wk",
        DAYS_PER_WEEK,
        bad_when_up=False,
    ),
    _MetricView(
        "push-frequency",
        METRIC_PUSHES_PER_DAY,
        "Push frequency",
        "/wk",
        DAYS_PER_WEEK,
        bad_when_up=False,
    ),
    _MetricView(
        "pr-review-time",
        METRIC_REVIEW_TIME_HOURS,
        "PR review time",
        "d",
        1.0 / HOURS_PER_DAY,
        bad_when_up=True,
    ),
)


def _direction(delta: float) -> MetricDirection:
    if delta > 1.0:
        return "up"
    if delta < -1.0:
        return "down"
    return "flat"


def _trend(delta: float, *, bad_when_up: bool) -> MetricTrend:
    """Amber/red only when the metric moved the wrong way, and moved a lot."""
    moved_badly = delta > 0 if bad_when_up else delta < 0
    if not moved_badly:
        return "good"
    magnitude = abs(delta)
    if magnitude >= BAD_DELTA_PERCENT:
        return "bad"
    if magnitude >= CAUTION_DELTA_PERCENT:
        return "caution"
    return "good"


def _percent_delta(value: float, baseline: float) -> float:
    if baseline == 0:
        return 0.0
    return (value - baseline) / baseline * 100.0


def _recent_mean(
    conn: duckdb.DuckDBPyConnection, team: str, metric: str, since: date, until: date
) -> float | None:
    """Mean of a metric over a window, ignoring days with no data."""
    series = get_metric_series(conn, team, metric, since, until)
    if not series:
        return None
    return sum(row.value for row in series) / len(series)


def _on_goal_metric(
    conn: duckdb.DuckDBPyConnection, team: str, now: datetime
) -> MetricOut | None:
    """Share of recent commits that reference tracked work, versus the prior window."""
    window = timedelta(days=MEMBER_WINDOW_DAYS)
    current = get_member_stats(conn, team, now - window)
    if not current:
        return None

    def share(rows: list[MemberStatsRow]) -> float | None:
        total = sum(r.commit_count for r in rows)
        if total == 0:
            return None
        return sum(r.linked_commit_count for r in rows) / total * 100.0

    value = share(current)
    if value is None:
        return None

    # Prior window = everything from two windows back, minus the current window.
    previous_rows = get_member_stats(conn, team, now - 2 * window)
    previous_total = sum(r.commit_count for r in previous_rows) - sum(
        r.commit_count for r in current
    )
    previous_linked = sum(r.linked_commit_count for r in previous_rows) - sum(
        r.linked_commit_count for r in current
    )
    baseline = (
        previous_linked / previous_total * 100.0 if previous_total > 0 else value
    )
    delta = _percent_delta(value, baseline)

    return MetricOut(
        id="on-goal-commits",
        label="On-goal commits",
        unit="%",
        value=round(value, 1),
        baseline=round(baseline, 1),
        delta=round(delta, 0),
        direction=_direction(delta),
        trend=_trend(delta, bad_when_up=False),
    )


def build_team_metrics(
    conn: duckdb.DuckDBPyConnection, team: str, now: datetime | None = None
) -> TeamMetricsOut:
    """The four KPI cards plus the 30-day review-time line."""
    now = now or utcnow()
    today = now.date()
    tomorrow = today + timedelta(days=1)

    metrics: list[MetricOut] = []
    for view in _METRIC_VIEWS:
        # "Current" is the trailing week, not a single day: one quiet Friday is
        # not a signal, and the KPI card should not flicker because of it.
        current = _recent_mean(
            conn, team, view.metric, today - timedelta(days=7), tomorrow
        )
        if current is None:
            continue
        baseline_stats = get_rolling_baseline(
            conn, team, view.metric, today - timedelta(days=7), BASELINE_WINDOW_DAYS
        )
        baseline = baseline_stats.mean if baseline_stats else current

        value_display = current * view.scale
        baseline_display = baseline * view.scale
        delta = _percent_delta(value_display, baseline_display)

        metrics.append(
            MetricOut(
                id=view.id,
                label=view.label,
                unit=view.unit,
                value=round(value_display, 1),
                baseline=round(baseline_display, 1),
                delta=round(delta, 0),
                direction=_direction(delta),
                trend=_trend(delta, bad_when_up=view.bad_when_up),
            )
        )

    on_goal = _on_goal_metric(conn, team, now)
    if on_goal is not None:
        metrics.append(on_goal)

    return TeamMetricsOut(
        metrics=metrics,
        review_time_history=build_review_time_history(conn, team, now),
    )


def build_review_time_history(
    conn: duckdb.DuckDBPyConnection, team: str, now: datetime | None = None
) -> list[ReviewTimePointOut]:
    now = now or utcnow()
    today = now.date()
    since = today - timedelta(days=REVIEW_HISTORY_DAYS - 1)
    series = get_metric_series(
        conn, team, METRIC_REVIEW_TIME_HOURS, since, today + timedelta(days=1)
    )
    if not series:
        return []

    baseline_stats = get_rolling_baseline(
        conn, team, METRIC_REVIEW_TIME_HOURS, since, BASELINE_WINDOW_DAYS
    )
    baseline_days = (
        baseline_stats.mean / HOURS_PER_DAY
        if baseline_stats
        else sum(r.value for r in series) / len(series) / HOURS_PER_DAY
    )

    return [
        ReviewTimePointOut(
            date=row.day.isoformat(),
            review_time_days=round(row.value / HOURS_PER_DAY, 2),
            baseline_days=round(baseline_days, 2),
        )
        for row in series
    ]


# --- anomalies --------------------------------------------------------------


def _anomaly_out(event: AnomalyEventRow) -> AnomalyOut:
    severity: AnomalySeverity = (
        event.severity if event.severity in ("info", "warning", "critical") else "info"
    )
    return AnomalyOut(
        id=slugify(event.id),
        team_id=slugify(event.team),
        severity=severity,
        title=event.title,
        description=event.description,
        detected_at=event.detected_at,
    )


_SEVERITY_RANK = {"critical": 0, "warning": 1, "info": 2}


def build_anomalies(
    conn: duckdb.DuckDBPyConnection, team: str | None = None
) -> list[AnomalyOut]:
    """Open anomalies, worst first, then most recent."""
    events = get_open_anomaly_events(conn, team)
    events.sort(
        key=lambda e: (_SEVERITY_RANK.get(e.severity, 3), -e.detected_at.timestamp())
    )
    return [_anomaly_out(event) for event in events]


# --- Phi-4 summary ----------------------------------------------------------


def build_summary(
    conn: duckdb.DuckDBPyConnection, team: str
) -> TeamSummaryOut | None:
    """The cached Phi-4 verdict for a team, or None if none has been generated."""
    row = get_summary(conn, team)
    if row is None:
        return None

    try:
        steps = json.loads(row.remediation_steps)
    except (TypeError, ValueError):
        steps = []
    suggestions = [str(step) for step in steps if str(step).strip()]
    if not suggestions:
        # The schema promises at least one suggestion; fall back to the verify
        # signal rather than shipping an empty chip row.
        suggestions = [row.verify_signal or "Keep monitoring this team"]

    return TeamSummaryOut(
        id=f"{slugify(team)}-summary-{row.generated_at.date().isoformat()}",
        team_id=slugify(team),
        model="Phi-4",
        summary=row.summary,
        suggestions=suggestions,
        generated_at=row.generated_at,
    )
