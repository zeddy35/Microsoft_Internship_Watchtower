"""Roll raw commits/pushes/PRs up into the daily series the engine reads.

The anomaly engine never touches the raw tables: it compares today's value of
a named metric against a rolling baseline in `metrics_daily`. This module is
what fills that table, and it runs on every refresh.

Two rules matter here:

- Commit and push series are **zero-filled**. A team that shipped nothing on
  Tuesday really did zero, and dropping the day would quietly lift the
  baseline instead of lowering it, hiding exactly the outage we want to catch.
- The review-time series is **not** zero-filled. A day with no reviewed PR is
  missing data, not a zero-hour review, so those days stay absent.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import duckdb

from app.anomaly.engine import (
    METRIC_COMMITS_PER_DAY,
    METRIC_PUSHES_PER_DAY,
    METRIC_REVIEW_TIME_HOURS,
)
from app.core.clock import utctoday
from app.core.db import (
    DailyValueRow,
    MetricDailyRow,
    get_active_days,
    get_daily_commit_counts,
    get_daily_push_counts,
    get_daily_review_time_hours,
    list_teams,
    upsert_metrics_daily,
)

DEFAULT_ROLLUP_DAYS = 120


@dataclass(frozen=True, slots=True)
class RollupResult:
    rows_written: int
    teams: int
    since: date
    until: date


def _zero_filled(
    team: str,
    metric: str,
    values: dict[date, float],
    days: list[date],
) -> list[MetricDailyRow]:
    """One row per day the team was observable, missing days counted as zero."""
    return [
        MetricDailyRow(team=team, metric=metric, day=day, value=values.get(day, 0.0))
        for day in days
    ]


def _observable_days(
    conn: duckdb.DuckDBPyConnection, team: str, since: date, until: date
) -> list[date]:
    """Every day from the team's first observed commit up to `until`.

    Before that first commit we simply had no data for the team, and inventing
    zeros there would fabricate a fake collapse at the start of every series.
    """
    active = get_active_days(conn, team, since, until)
    if not active:
        return []
    start = active[0]
    span = (until - start).days
    return [start + timedelta(days=offset) for offset in range(span)]


def _group_by_team(rows: list[DailyValueRow]) -> dict[str, dict[date, float]]:
    grouped: dict[str, dict[date, float]] = {}
    for row in rows:
        grouped.setdefault(row.team, {})[row.day] = row.value
    return grouped


def rollup_metrics(
    conn: duckdb.DuckDBPyConnection,
    *,
    days: int = DEFAULT_ROLLUP_DAYS,
    until: date | None = None,
) -> RollupResult:
    """Recompute `metrics_daily` for the trailing window and store it.

    `until` is exclusive; it defaults to tomorrow so today is always included.
    """
    until = until or (utctoday() + timedelta(days=1))
    since = until - timedelta(days=days)

    commits_by_team = _group_by_team(get_daily_commit_counts(conn, since, until))
    pushes_by_team = _group_by_team(get_daily_push_counts(conn, since, until))
    review_by_team = _group_by_team(get_daily_review_time_hours(conn, since, until))

    rows: list[MetricDailyRow] = []
    teams = list_teams(conn)
    for team in teams:
        days_observed = _observable_days(conn, team, since, until)
        if days_observed:
            rows.extend(
                _zero_filled(
                    team,
                    METRIC_COMMITS_PER_DAY,
                    commits_by_team.get(team, {}),
                    days_observed,
                )
            )
            rows.extend(
                _zero_filled(
                    team,
                    METRIC_PUSHES_PER_DAY,
                    pushes_by_team.get(team, {}),
                    days_observed,
                )
            )

        # Review time keeps its gaps on purpose (see the module docstring).
        rows.extend(
            MetricDailyRow(
                team=team, metric=METRIC_REVIEW_TIME_HOURS, day=day, value=value
            )
            for day, value in sorted(review_by_team.get(team, {}).items())
        )

    upsert_metrics_daily(conn, rows)
    return RollupResult(
        rows_written=len(rows), teams=len(teams), since=since, until=until
    )
