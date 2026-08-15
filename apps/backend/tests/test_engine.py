"""Anomaly engine: synthetic series in, the right flags out."""

from __future__ import annotations

from datetime import date, timedelta

from app.anomaly.engine import (
    METRIC_COMMITS_PER_DAY,
    METRIC_REVIEW_TIME_HOURS,
    TRACKED_METRICS,
    Severity,
    detect_team_anomalies,
    evaluate_metric,
    evaluate_stale_prs,
)
from app.core.db import MetricDailyRow, upsert_metrics_daily, upsert_repo
from app.metrics.rollup import rollup_metrics
from tests.conftest import NOW, REPO, TEAM

COMMITS_SPEC = next(s for s in TRACKED_METRICS if s.metric == METRIC_COMMITS_PER_DAY)
REVIEW_SPEC = next(s for s in TRACKED_METRICS if s.metric == METRIC_REVIEW_TIME_HOURS)

START = date(2026, 7, 1)


def _write_series(conn, metric, values):
    upsert_metrics_daily(
        conn,
        [
            MetricDailyRow(TEAM, metric, START + timedelta(days=index), value)
            for index, value in enumerate(values)
        ],
    )
    return START + timedelta(days=len(values) - 1)


def test_commit_drop_is_flagged_critical(conn):
    upsert_repo(conn, REPO, team=TEAM)
    last_day = _write_series(conn, METRIC_COMMITS_PER_DAY, [10, 11, 9, 10, 12, 10, 0])

    anomaly = evaluate_metric(
        conn, TEAM, COMMITS_SPEC, last_day + timedelta(days=1), NOW
    )

    assert anomaly is not None
    assert anomaly.severity is Severity.CRITICAL
    assert anomaly.observed == 0.0
    assert anomaly.z_score < 0
    assert "dropped" in anomaly.title.lower()


def test_commit_surge_is_not_an_anomaly(conn):
    """A good week is not a problem: direction matters, not just distance."""
    upsert_repo(conn, REPO, team=TEAM)
    last_day = _write_series(conn, METRIC_COMMITS_PER_DAY, [10, 11, 9, 10, 12, 10, 40])

    assert (
        evaluate_metric(conn, TEAM, COMMITS_SPEC, last_day + timedelta(days=1), NOW)
        is None
    )


def test_review_time_spike_is_flagged(conn):
    upsert_repo(conn, REPO, team=TEAM)
    last_day = _write_series(
        conn, METRIC_REVIEW_TIME_HOURS, [6, 5, 7, 6, 6, 5.5, 96]
    )

    anomaly = evaluate_metric(
        conn, TEAM, REVIEW_SPEC, last_day + timedelta(days=1), NOW
    )

    assert anomaly is not None
    assert anomaly.severity is Severity.CRITICAL
    assert "spiked" in anomaly.title.lower()


def test_short_history_is_not_enough_to_flag(conn):
    """Two data points cannot establish a baseline, so nothing is claimed."""
    upsert_repo(conn, REPO, team=TEAM)
    last_day = _write_series(conn, METRIC_COMMITS_PER_DAY, [10, 0])

    assert (
        evaluate_metric(conn, TEAM, COMMITS_SPEC, last_day + timedelta(days=1), NOW)
        is None
    )


def test_flat_series_never_flags(conn):
    """Zero variance means an undefined z-score, not an infinite one."""
    upsert_repo(conn, REPO, team=TEAM)
    last_day = _write_series(conn, METRIC_COMMITS_PER_DAY, [10] * 8)

    assert (
        evaluate_metric(conn, TEAM, COMMITS_SPEC, last_day + timedelta(days=1), NOW)
        is None
    )


def test_stale_prs_are_flagged_from_raw_rows(seeded):
    anomaly = evaluate_stale_prs(seeded, TEAM, NOW)

    assert anomaly is not None
    assert anomaly.metric == "stale_prs"
    assert anomaly.severity is Severity.CRITICAL  # open 21 days, past 2x threshold
    assert "#2001" in anomaly.description


def test_detect_team_anomalies_sorts_worst_first(seeded):
    rollup_metrics(seeded, until=(NOW + timedelta(days=1)).date())

    anomalies = detect_team_anomalies(seeded, TEAM, now=NOW)

    assert anomalies
    severities = [a.severity for a in anomalies]
    assert severities == sorted(
        severities, key=lambda s: {"critical": 0, "warning": 1, "info": 2}[s.value]
    )
    assert any(a.metric == METRIC_COMMITS_PER_DAY for a in anomalies)
