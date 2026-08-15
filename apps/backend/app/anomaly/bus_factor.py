"""Bus-factor calculator: how concentrated is a team's work in one person?

For each of a team's code areas (repos, since DuckDB stores commits at repo
granularity) we measure the top contributor's share of recent commits. A high
share means the area has a low bus factor — losing one person would hurt.
Risk buckets: High >70%, Medium 50-70%, Low <50% ownership.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

import duckdb

from app.core.clock import utcnow
from app.core.db import get_commit_ownership, list_teams

DEFAULT_LOOKBACK_DAYS = 90
HIGH_RISK_THRESHOLD = 70.0  # top owner holds > this share -> High risk
MEDIUM_RISK_THRESHOLD = 50.0  # 50-70% -> Medium risk


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class BusFactorArea:
    area: str
    top_owner: str
    ownership_percent: float
    total_commits: int
    contributor_count: int
    last_activity: datetime
    risk_level: RiskLevel


def _risk_for_share(ownership_percent: float) -> RiskLevel:
    if ownership_percent > HIGH_RISK_THRESHOLD:
        return RiskLevel.HIGH
    if ownership_percent >= MEDIUM_RISK_THRESHOLD:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def compute_team_bus_factor(
    conn: duckdb.DuckDBPyConnection,
    team: str,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    now: datetime | None = None,
) -> list[BusFactorArea]:
    """One BusFactorArea per repo the team has committed to in the window."""
    now = now or utcnow()
    since = now - timedelta(days=lookback_days)
    rows = get_commit_ownership(conn, team, since)

    # Group ownership rows by repo (they arrive ordered repo, count desc).
    by_repo: dict[str, list] = {}
    for row in rows:
        by_repo.setdefault(row.repo, []).append(row)

    areas: list[BusFactorArea] = []
    for repo, owners in by_repo.items():
        total = sum(o.commit_count for o in owners)
        if total == 0:
            continue
        top = max(owners, key=lambda o: o.commit_count)
        share = top.commit_count / total * 100.0
        last_activity = max(o.last_committed_at for o in owners)
        areas.append(
            BusFactorArea(
                area=repo,
                top_owner=top.author,
                ownership_percent=round(share, 1),
                total_commits=total,
                contributor_count=len(owners),
                last_activity=last_activity,
                risk_level=_risk_for_share(share),
            )
        )

    # Riskiest areas first.
    risk_rank = {RiskLevel.HIGH: 0, RiskLevel.MEDIUM: 1, RiskLevel.LOW: 2}
    areas.sort(key=lambda a: (risk_rank[a.risk_level], -a.ownership_percent))
    return areas


def compute_all_bus_factors(
    conn: duckdb.DuckDBPyConnection,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    now: datetime | None = None,
) -> dict[str, list[BusFactorArea]]:
    """Bus-factor areas for every registered team, keyed by team."""
    return {
        team: compute_team_bus_factor(conn, team, lookback_days, now)
        for team in list_teams(conn)
    }
