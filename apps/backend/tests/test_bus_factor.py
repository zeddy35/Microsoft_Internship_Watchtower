"""Bus factor: ownership concentration into risk buckets."""

from __future__ import annotations

from datetime import timedelta

from app.anomaly.bus_factor import RiskLevel, compute_team_bus_factor
from app.core.db import CommitRow, insert_commits, upsert_repo
from tests.conftest import NOW, REPO, TEAM


def _commits(conn, authors_by_count: dict[str, int]) -> None:
    upsert_repo(conn, REPO, team=TEAM)
    rows = []
    index = 0
    for author, count in authors_by_count.items():
        for _ in range(count):
            rows.append(
                CommitRow(
                    sha=f"sha-{index}",
                    repo=REPO,
                    author=author,
                    message="Work",
                    additions=1,
                    deletions=0,
                    committed_at=NOW - timedelta(days=1),
                )
            )
            index += 1
    insert_commits(conn, rows)


def test_single_owner_is_high_risk(conn):
    _commits(conn, {"elena": 9, "raj": 1})

    areas = compute_team_bus_factor(conn, TEAM, now=NOW)

    assert len(areas) == 1
    assert areas[0].top_owner == "elena"
    assert areas[0].ownership_percent == 90.0
    assert areas[0].risk_level is RiskLevel.HIGH
    assert areas[0].contributor_count == 2


def test_even_split_is_low_risk(conn):
    _commits(conn, {"elena": 4, "raj": 4, "wei": 4})

    areas = compute_team_bus_factor(conn, TEAM, now=NOW)

    assert areas[0].risk_level is RiskLevel.LOW


def test_the_medium_band_starts_at_fifty_percent(conn):
    _commits(conn, {"elena": 5, "raj": 3, "wei": 2})

    areas = compute_team_bus_factor(conn, TEAM, now=NOW)

    assert areas[0].ownership_percent == 50.0
    assert areas[0].risk_level is RiskLevel.MEDIUM


def test_commits_outside_the_window_are_ignored(conn):
    upsert_repo(conn, REPO, team=TEAM)
    insert_commits(
        conn,
        [
            CommitRow(
                sha="old",
                repo=REPO,
                author="elena",
                message="Ancient history",
                additions=1,
                deletions=0,
                committed_at=NOW - timedelta(days=400),
            )
        ],
    )

    assert compute_team_bus_factor(conn, TEAM, now=NOW) == []
