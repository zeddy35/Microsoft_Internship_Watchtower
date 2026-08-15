"""DuckDB helpers: idempotent writes, correct windows, honest aggregates."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta

from app.core.db import (
    CommitRow,
    MetricDailyRow,
    SummaryRow,
    anomaly_event_id,
    clear_anomaly_event,
    get_daily_commit_counts,
    get_daily_review_time_hours,
    get_member_stats,
    get_metric_series,
    get_open_anomaly_events,
    get_rolling_baseline,
    get_stale_open_prs,
    get_summary,
    get_unnotified_events,
    insert_commits,
    insert_resolution,
    list_resolutions,
    list_teams,
    mark_events_notified,
    upsert_anomaly_event,
    upsert_metrics_daily,
    upsert_summary,
)
from tests.conftest import NOW, REPO, TEAM


def test_insert_commits_is_idempotent(conn):
    row = CommitRow(
        sha="abc",
        repo=REPO,
        author="elena",
        message="Fix #1",
        additions=1,
        deletions=0,
        committed_at=NOW,
    )
    insert_commits(conn, [row])
    insert_commits(conn, [row])

    assert conn.execute("SELECT count(*) FROM commits").fetchone()[0] == 1


def test_upsert_metrics_daily_overwrites_the_same_day(conn):
    day = date(2026, 8, 1)
    upsert_metrics_daily(conn, [MetricDailyRow(TEAM, "commits_per_day", day, 3.0)])
    upsert_metrics_daily(conn, [MetricDailyRow(TEAM, "commits_per_day", day, 9.0)])

    series = get_metric_series(conn, TEAM, "commits_per_day", day, day + timedelta(1))
    assert [row.value for row in series] == [9.0]


def test_rolling_baseline_excludes_the_day_it_is_measured_from(conn):
    start = date(2026, 8, 1)
    rows = [
        MetricDailyRow(TEAM, "commits_per_day", start + timedelta(days=i), 10.0)
        for i in range(5)
    ]
    # The day we ask about is an outlier and must not pull its own baseline.
    rows.append(MetricDailyRow(TEAM, "commits_per_day", start + timedelta(days=5), 0.0))
    upsert_metrics_daily(conn, rows)

    stats = get_rolling_baseline(
        conn, TEAM, "commits_per_day", start + timedelta(days=5), window_days=28
    )
    assert stats is not None
    assert stats.mean == 10.0
    assert stats.sample_size == 5


def test_daily_commit_counts_group_by_day(seeded):
    rows = get_daily_commit_counts(
        seeded, (NOW - timedelta(days=60)).date(), (NOW + timedelta(days=1)).date()
    )
    assert rows
    assert all(row.team == TEAM for row in rows)
    assert all(row.value > 0 for row in rows)


def test_daily_review_time_skips_unreviewed_prs(seeded):
    rows = get_daily_review_time_hours(
        seeded, (NOW - timedelta(days=60)).date(), (NOW + timedelta(days=1)).date()
    )
    # Every seeded reviewed PR was reviewed six hours after opening.
    assert rows
    assert all(abs(row.value - 6.0) < 1e-6 for row in rows)


def test_stale_open_prs_finds_the_unreviewed_one(seeded):
    stale = get_stale_open_prs(seeded, TEAM, NOW, older_than_days=7)
    assert [row.id for row in stale] == [2001]
    assert stale[0].age_days == 21


def test_member_stats_counts_linked_commits(seeded):
    stats = get_member_stats(seeded, TEAM, NOW - timedelta(days=28))
    assert stats
    top = stats[0]
    assert top.commit_count > 0
    # Half the seeded messages reference an issue number, the rest do not.
    assert 0 < top.linked_commit_count < top.commit_count
    assert top.avg_review_hours is None or top.avg_review_hours > 0


def test_list_teams_returns_registered_teams(seeded):
    assert list_teams(seeded) == [TEAM]


def test_anomaly_event_lifecycle_writes_a_resolution(conn):
    event_id = upsert_anomaly_event(
        conn,
        team=TEAM,
        metric="commits_per_day",
        severity="critical",
        title="Commit volume dropped",
        description="...",
        observed=0.0,
        baseline=6.0,
        z_score=-4.0,
        seen_at=NOW,
    )
    assert event_id == anomaly_event_id(TEAM, "commits_per_day")

    # Re-detecting the same anomaly updates one row, it does not add a second.
    upsert_anomaly_event(
        conn,
        team=TEAM,
        metric="commits_per_day",
        severity="critical",
        title="Commit volume dropped",
        description="still down",
        observed=0.0,
        baseline=6.0,
        z_score=-4.2,
        seen_at=NOW + timedelta(hours=1),
    )
    open_events = get_open_anomaly_events(conn, TEAM)
    assert len(open_events) == 1
    assert open_events[0].detected_at == NOW  # first sighting is preserved

    clear_anomaly_event(conn, event_id, NOW + timedelta(days=2))
    insert_resolution(
        conn,
        anomaly_id=event_id,
        team=TEAM,
        metric="commits_per_day",
        severity="critical",
        action="Rebalance review load",
        outcome="cleared",
        detected_at=NOW,
        resolved_at=NOW + timedelta(days=2),
    )

    assert get_open_anomaly_events(conn, TEAM) == []
    resolutions = list_resolutions(conn, TEAM)
    assert len(resolutions) == 1
    assert resolutions[0].outcome == "cleared"
    assert abs(resolutions[0].open_days - 2.0) < 1e-6


def test_notification_guard_marks_events_once(conn):
    event_id = upsert_anomaly_event(
        conn,
        team=TEAM,
        metric="review_time_hours",
        severity="critical",
        title="Review time spiked",
        description="...",
        observed=90.0,
        baseline=6.0,
        z_score=4.0,
        seen_at=NOW,
    )
    assert [event.id for event in get_unnotified_events(conn, ("critical",))] == [
        event_id
    ]

    mark_events_notified(conn, [event_id], NOW)
    assert get_unnotified_events(conn, ("critical",)) == []


def test_summary_upsert_replaces_previous_verdict(conn):
    first = SummaryRow(
        team=TEAM,
        summary="old",
        root_cause="old",
        remediation_steps="[]",
        verify_signal="",
        on_goal_score=50.0,
        generated_at=NOW,
    )
    upsert_summary(conn, first)
    upsert_summary(conn, replace(first, summary="new"))

    stored = get_summary(conn, TEAM)
    assert stored is not None
    assert stored.summary == "new"
