"""Rollup: zero-fill the volume series, leave review-time gaps alone."""

from __future__ import annotations

from datetime import timedelta

from app.anomaly.engine import (
    METRIC_COMMITS_PER_DAY,
    METRIC_PUSHES_PER_DAY,
    METRIC_REVIEW_TIME_HOURS,
)
from app.core.db import get_metric_series
from app.metrics.rollup import rollup_metrics
from tests.conftest import NOW, QUIET_DAYS, TEAM


def _series(conn, metric):
    return get_metric_series(
        conn,
        TEAM,
        metric,
        (NOW - timedelta(days=90)).date(),
        (NOW + timedelta(days=1)).date(),
    )


def test_rollup_writes_all_three_metrics(seeded):
    result = rollup_metrics(seeded, until=(NOW + timedelta(days=1)).date())

    assert result.teams == 1
    assert result.rows_written > 0
    assert _series(seeded, METRIC_COMMITS_PER_DAY)
    assert _series(seeded, METRIC_PUSHES_PER_DAY)
    assert _series(seeded, METRIC_REVIEW_TIME_HOURS)


def test_quiet_days_are_stored_as_zero_not_dropped(seeded):
    """The whole point of zero-fill: silence has to be visible to the engine."""
    rollup_metrics(seeded, until=(NOW + timedelta(days=1)).date())

    series = _series(seeded, METRIC_COMMITS_PER_DAY)
    tail = series[-QUIET_DAYS:]

    assert len(tail) == QUIET_DAYS
    assert all(row.value == 0.0 for row in tail)
    assert series[-QUIET_DAYS - 1].value > 0


def test_review_time_series_keeps_its_gaps(seeded):
    """A day with no reviewed PR is missing data, not a zero-hour review."""
    rollup_metrics(seeded, until=(NOW + timedelta(days=1)).date())

    review = _series(seeded, METRIC_REVIEW_TIME_HOURS)
    commits = _series(seeded, METRIC_COMMITS_PER_DAY)

    assert len(review) < len(commits)
    assert all(row.value > 0 for row in review)


def test_rollup_is_idempotent(seeded):
    until = (NOW + timedelta(days=1)).date()
    first = rollup_metrics(seeded, until=until)
    second = rollup_metrics(seeded, until=until)

    assert first.rows_written == second.rows_written
    assert len(_series(seeded, METRIC_COMMITS_PER_DAY)) == first.rows_written - len(
        _series(seeded, METRIC_PUSHES_PER_DAY)
    ) - len(_series(seeded, METRIC_REVIEW_TIME_HOURS))
