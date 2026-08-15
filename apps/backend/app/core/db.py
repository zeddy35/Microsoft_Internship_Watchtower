"""DuckDB connection helper, schema init, and typed insert/query helpers.

Plain SQL with parameters, no ORM. `get_connection()` is a process-wide
singleton; callers pass the connection into every helper explicitly so
tests can inject a throwaway in-memory database instead.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from functools import lru_cache

import duckdb

from app.config import get_settings

# --- connection -----------------------------------------------------------


@lru_cache
def get_connection() -> duckdb.DuckDBPyConnection:
    """Process-wide DuckDB connection, opened once against DUCKDB_PATH."""
    settings = get_settings()
    settings.DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(settings.DUCKDB_PATH))
    init_schema(conn)
    return conn


def init_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Create all tables/sequences/indexes if they don't already exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS repos (
            repo TEXT PRIMARY KEY,
            team TEXT,
            last_synced_at TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS commits (
            sha TEXT PRIMARY KEY,
            repo TEXT NOT NULL,
            author TEXT NOT NULL,
            message TEXT NOT NULL,
            additions INTEGER NOT NULL DEFAULT 0,
            deletions INTEGER NOT NULL DEFAULT 0,
            committed_at TIMESTAMP NOT NULL
        )
    """)

    conn.execute("CREATE SEQUENCE IF NOT EXISTS pushes_id_seq START 1")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pushes (
            id BIGINT PRIMARY KEY DEFAULT nextval('pushes_id_seq'),
            repo TEXT NOT NULL,
            author TEXT NOT NULL,
            ref TEXT NOT NULL,
            pushed_at TIMESTAMP NOT NULL,
            UNIQUE (repo, author, ref, pushed_at)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS pull_requests (
            id BIGINT PRIMARY KEY,
            repo TEXT NOT NULL,
            author TEXT NOT NULL,
            opened_at TIMESTAMP NOT NULL,
            first_review_at TIMESTAMP,
            merged_at TIMESTAMP,
            state TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS metrics_daily (
            team TEXT NOT NULL,
            metric TEXT NOT NULL,
            day DATE NOT NULL,
            value DOUBLE NOT NULL,
            PRIMARY KEY (team, metric, day)
        )
    """)

    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_commits_repo_time "
        "ON commits (repo, committed_at)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_pushes_repo_time ON pushes (repo, pushed_at)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_prs_repo_time "
        "ON pull_requests (repo, opened_at)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_metrics_daily_team_metric "
        "ON metrics_daily (team, metric, day)"
    )


# --- row types --------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CommitRow:
    sha: str
    repo: str
    author: str
    message: str
    additions: int
    deletions: int
    committed_at: datetime


@dataclass(frozen=True, slots=True)
class PushRow:
    repo: str
    author: str
    ref: str
    pushed_at: datetime


@dataclass(frozen=True, slots=True)
class PullRequestRow:
    id: int
    repo: str
    author: str
    opened_at: datetime
    first_review_at: datetime | None
    merged_at: datetime | None
    state: str


@dataclass(frozen=True, slots=True)
class MetricDailyRow:
    team: str
    metric: str
    day: date
    value: float


@dataclass(frozen=True, slots=True)
class RollingStats:
    mean: float
    stddev: float
    sample_size: int


@dataclass(frozen=True, slots=True)
class StalePrRow:
    id: int
    repo: str
    author: str
    opened_at: datetime
    age_days: int


@dataclass(frozen=True, slots=True)
class OwnershipRow:
    repo: str
    author: str
    commit_count: int
    last_committed_at: datetime


# --- repos --------------------------------------------------------------


def upsert_repo(
    conn: duckdb.DuckDBPyConnection, repo: str, team: str | None = None
) -> None:
    conn.execute(
        "INSERT INTO repos (repo, team) VALUES (?, ?) "
        "ON CONFLICT (repo) DO UPDATE SET team = COALESCE(excluded.team, repos.team)",
        [repo, team],
    )


def update_repo_synced_at(
    conn: duckdb.DuckDBPyConnection, repo: str, synced_at: datetime
) -> None:
    conn.execute(
        "UPDATE repos SET last_synced_at = ? WHERE repo = ?", [synced_at, repo]
    )


def get_repo_last_synced_at(
    conn: duckdb.DuckDBPyConnection, repo: str
) -> datetime | None:
    row = conn.execute(
        "SELECT last_synced_at FROM repos WHERE repo = ?", [repo]
    ).fetchone()
    return row[0] if row else None


def list_teams(conn: duckdb.DuckDBPyConnection) -> list[str]:
    rows = conn.execute(
        "SELECT DISTINCT team FROM repos WHERE team IS NOT NULL ORDER BY team"
    ).fetchall()
    return [row[0] for row in rows]


def get_team_repos(conn: duckdb.DuckDBPyConnection, team: str) -> list[str]:
    rows = conn.execute(
        "SELECT repo FROM repos WHERE team = ? ORDER BY repo", [team]
    ).fetchall()
    return [row[0] for row in rows]


# --- commits / pushes / pull requests --------------------------------------


def insert_commits(
    conn: duckdb.DuckDBPyConnection, commits: Sequence[CommitRow]
) -> None:
    if not commits:
        return
    conn.executemany(
        "INSERT INTO commits "
        "(sha, repo, author, message, additions, deletions, committed_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT (sha) DO NOTHING",
        [
            (c.sha, c.repo, c.author, c.message, c.additions, c.deletions, c.committed_at)
            for c in commits
        ],
    )


def insert_pushes(conn: duckdb.DuckDBPyConnection, pushes: Sequence[PushRow]) -> None:
    if not pushes:
        return
    conn.executemany(
        "INSERT INTO pushes (repo, author, ref, pushed_at) VALUES (?, ?, ?, ?) "
        "ON CONFLICT (repo, author, ref, pushed_at) DO NOTHING",
        [(p.repo, p.author, p.ref, p.pushed_at) for p in pushes],
    )


def upsert_pull_requests(
    conn: duckdb.DuckDBPyConnection, pull_requests: Sequence[PullRequestRow]
) -> None:
    if not pull_requests:
        return
    conn.executemany(
        "INSERT INTO pull_requests "
        "(id, repo, author, opened_at, first_review_at, merged_at, state) "
        "VALUES (?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT (id) DO UPDATE SET "
        "first_review_at = excluded.first_review_at, "
        "merged_at = excluded.merged_at, "
        "state = excluded.state",
        [
            (pr.id, pr.repo, pr.author, pr.opened_at, pr.first_review_at, pr.merged_at, pr.state)
            for pr in pull_requests
        ],
    )


# --- metrics_daily --------------------------------------------------------


def upsert_metrics_daily(
    conn: duckdb.DuckDBPyConnection, rows: Sequence[MetricDailyRow]
) -> None:
    if not rows:
        return
    conn.executemany(
        "INSERT INTO metrics_daily (team, metric, day, value) VALUES (?, ?, ?, ?) "
        "ON CONFLICT (team, metric, day) DO UPDATE SET value = excluded.value",
        [(r.team, r.metric, r.day, r.value) for r in rows],
    )


def get_metric_series(
    conn: duckdb.DuckDBPyConnection,
    team: str,
    metric: str,
    since: date,
    until: date | None = None,
) -> list[MetricDailyRow]:
    """Daily values for a team/metric within [since, until), ordered by day."""
    rows = conn.execute(
        "SELECT team, metric, day, value FROM metrics_daily "
        "WHERE team = ? AND metric = ? AND day >= ? AND (? IS NULL OR day < ?) "
        "ORDER BY day",
        [team, metric, since, until, until],
    ).fetchall()
    return [MetricDailyRow(*row) for row in rows]


def get_rolling_baseline(
    conn: duckdb.DuckDBPyConnection,
    team: str,
    metric: str,
    as_of: date,
    window_days: int,
) -> RollingStats | None:
    """Mean + stddev over the trailing window ending just before as_of."""
    row = conn.execute(
        "SELECT avg(value), stddev_samp(value), count(*) FROM metrics_daily "
        "WHERE team = ? AND metric = ? AND day >= ? AND day < ?",
        [team, metric, as_of - timedelta(days=window_days), as_of],
    ).fetchone()
    if row is None or row[2] == 0:
        return None
    mean, stddev, sample_size = row
    return RollingStats(mean=mean, stddev=stddev or 0.0, sample_size=sample_size)


# --- per-team aggregates over raw tables ------------------------------------


def get_commit_counts_by_team(
    conn: duckdb.DuckDBPyConnection, since: datetime, until: datetime | None = None
) -> dict[str, int]:
    rows = conn.execute(
        "SELECT r.team, count(*) FROM commits c JOIN repos r ON c.repo = r.repo "
        "WHERE r.team IS NOT NULL AND c.committed_at >= ? "
        "AND (? IS NULL OR c.committed_at < ?) "
        "GROUP BY r.team",
        [since, until, until],
    ).fetchall()
    return dict(rows)


def get_push_counts_by_team(
    conn: duckdb.DuckDBPyConnection, since: datetime, until: datetime | None = None
) -> dict[str, int]:
    rows = conn.execute(
        "SELECT r.team, count(*) FROM pushes p JOIN repos r ON p.repo = r.repo "
        "WHERE r.team IS NOT NULL AND p.pushed_at >= ? "
        "AND (? IS NULL OR p.pushed_at < ?) "
        "GROUP BY r.team",
        [since, until, until],
    ).fetchall()
    return dict(rows)


def get_avg_review_time_hours_by_team(
    conn: duckdb.DuckDBPyConnection, since: datetime, until: datetime | None = None
) -> dict[str, float]:
    """Average hours from opened_at to first_review_at, for PRs opened in range."""
    rows = conn.execute(
        "SELECT r.team, avg(date_diff('hour', p.opened_at, p.first_review_at)) "
        "FROM pull_requests p JOIN repos r ON p.repo = r.repo "
        "WHERE r.team IS NOT NULL AND p.first_review_at IS NOT NULL "
        "AND p.opened_at >= ? AND (? IS NULL OR p.opened_at < ?) "
        "GROUP BY r.team",
        [since, until, until],
    ).fetchall()
    return dict(rows)


# --- helpers for the anomaly engine + bus factor ---------------------------


def get_latest_metric(
    conn: duckdb.DuckDBPyConnection,
    team: str,
    metric: str,
    as_of: date | None = None,
) -> MetricDailyRow | None:
    """Most recent stored value for a team/metric, on or before as_of."""
    row = conn.execute(
        "SELECT team, metric, day, value FROM metrics_daily "
        "WHERE team = ? AND metric = ? AND (? IS NULL OR day <= ?) "
        "ORDER BY day DESC LIMIT 1",
        [team, metric, as_of, as_of],
    ).fetchone()
    return MetricDailyRow(*row) if row else None


def get_stale_open_prs(
    conn: duckdb.DuckDBPyConnection,
    team: str,
    as_of: datetime,
    older_than_days: int = 7,
) -> list[StalePrRow]:
    """Open, unmerged PRs for a team's repos opened more than N days before as_of."""
    cutoff = as_of - timedelta(days=older_than_days)
    rows = conn.execute(
        "SELECT p.id, p.repo, p.author, p.opened_at, "
        "date_diff('day', p.opened_at, ?) AS age_days "
        "FROM pull_requests p JOIN repos r ON p.repo = r.repo "
        "WHERE r.team = ? AND p.merged_at IS NULL AND p.state = 'open' "
        "AND p.opened_at < ? "
        "ORDER BY p.opened_at",
        [as_of, team, cutoff],
    ).fetchall()
    return [StalePrRow(*row) for row in rows]


def get_commit_ownership(
    conn: duckdb.DuckDBPyConnection, team: str, since: datetime
) -> list[OwnershipRow]:
    """Per-repo, per-author commit counts + last activity for a team, since a cutoff.

    Repos stand in for "code areas": DuckDB stores commits at repo granularity,
    not per-file, so bus-factor concentration is measured across a team's repos.
    """
    rows = conn.execute(
        "SELECT c.repo, c.author, count(*) AS commit_count, "
        "max(c.committed_at) AS last_committed_at "
        "FROM commits c JOIN repos r ON c.repo = r.repo "
        "WHERE r.team = ? AND c.committed_at >= ? "
        "GROUP BY c.repo, c.author "
        "ORDER BY c.repo, commit_count DESC",
        [team, since],
    ).fetchall()
    return [OwnershipRow(*row) for row in rows]
