"""The demo seeder: every table filled, and filled with what the engine finds."""

from __future__ import annotations

from app.core.db import (
    DATA_SOURCE_DEMO,
    SETTING_DATA_SOURCE,
    get_open_anomaly_events,
    get_setting,
    get_summary,
    list_resolutions,
    list_teams,
)
from app.jobs import run_anomaly_pass
from app.metrics.rollup import rollup_metrics
from app.seed.demo import PROFILES, clear_demo_data, seed_demo_data
from tests.conftest import NOW


def _seed(conn):
    result = seed_demo_data(conn, now=NOW)
    rollup_metrics(conn, until=(NOW.date()))
    run_anomaly_pass(conn, now=NOW)
    return result


def test_seeder_fills_every_table(conn):
    result = _seed(conn)

    assert result.teams == len(PROFILES)
    assert result.commits > 500
    assert result.pushes > 100
    assert result.pull_requests > 30
    assert len(list_teams(conn)) == len(PROFILES)
    assert list_resolutions(conn)
    assert all(get_summary(conn, team) is not None for team in list_teams(conn))


def test_seeded_anomalies_come_from_the_real_engine(conn):
    """The demo must show what Watchtower detects, not a picture of it."""
    _seed(conn)

    events = get_open_anomaly_events(conn)
    assert events

    by_team: dict[str, list[str]] = {}
    for event in events:
        by_team.setdefault(event.team, []).append(event.severity)

    # The team seeded as collapsing is flagged; the healthy one is not.
    assert "Azure Core Networking" in by_team
    assert "critical" in by_team["Azure Core Networking"]
    assert "M365 Copilot Extensibility" not in by_team


def test_seeding_marks_the_data_source_as_demo(conn):
    """A dashboard that cannot say where its numbers came from is worse than empty."""
    _seed(conn)

    assert get_setting(conn, SETTING_DATA_SOURCE) == DATA_SOURCE_DEMO


def test_seeder_is_deterministic(conn):
    first = _seed(conn)
    clear_demo_data(conn)
    second = _seed(conn)

    assert first == second


def test_resolutions_carry_the_advice_that_was_live(conn):
    _seed(conn)

    resolutions = list_resolutions(conn)
    assert resolutions
    assert all(row.outcome == "cleared" for row in resolutions)
    assert all(row.action for row in resolutions)
    assert all(row.open_days > 0 for row in resolutions)
