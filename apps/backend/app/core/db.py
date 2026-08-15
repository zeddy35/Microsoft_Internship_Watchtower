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

    # Every anomaly the engine has ever flagged, keyed by a stable
    # team+metric id so repeated passes update one row instead of piling up.
    # `cleared_at` is what the verify pass writes when the anomaly goes away.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS anomaly_events (
            id TEXT PRIMARY KEY,
            team TEXT NOT NULL,
            metric TEXT NOT NULL,
            severity TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            observed DOUBLE NOT NULL,
            baseline DOUBLE NOT NULL,
            z_score DOUBLE NOT NULL,
            detected_at TIMESTAMP NOT NULL,
            last_seen_at TIMESTAMP NOT NULL,
            cleared_at TIMESTAMP,
            notified_at TIMESTAMP
        )
    """)

    # Labeled outcomes: one row per anomaly that closed, with how long it
    # stayed open and what Watchtower had recommended. This is the training
    # set the predictive layer (P1) learns from.
    conn.execute("CREATE SEQUENCE IF NOT EXISTS resolutions_id_seq START 1")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS resolutions (
            id BIGINT PRIMARY KEY DEFAULT nextval('resolutions_id_seq'),
            anomaly_id TEXT NOT NULL,
            team TEXT NOT NULL,
            metric TEXT NOT NULL,
            severity TEXT NOT NULL,
            action TEXT NOT NULL,
            outcome TEXT NOT NULL,
            detected_at TIMESTAMP NOT NULL,
            resolved_at TIMESTAMP NOT NULL,
            open_days DOUBLE NOT NULL
        )
    """)

    # Latest Phi-4 verdict per team, written by the scheduled resolver pass so
    # the API can answer instantly instead of blocking on local inference.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            team TEXT PRIMARY KEY,
            summary TEXT NOT NULL,
            root_cause TEXT NOT NULL,
            remediation_steps TEXT NOT NULL,
            verify_signal TEXT NOT NULL,
            on_goal_score DOUBLE NOT NULL,
            generated_at TIMESTAMP NOT NULL
        )
    """)

    # Operator-facing configuration that should outlive a process restart and
    # be editable from the Settings page. Secrets never live here: the GitHub
    # token stays in .env, and this table only ever holds non-sensitive
    # configuration like which repos to watch.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP NOT NULL
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
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_anomaly_events_team "
        "ON anomaly_events (team, cleared_at)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_resolutions_team ON resolutions (team)"
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


@dataclass(frozen=True, slots=True)
class CommitDocRow:
    sha: str
    repo: str
    author: str
    message: str
    committed_at: datetime


def get_commit_docs_for_team(
    conn: duckdb.DuckDBPyConnection,
    team: str,
    since: datetime,
    limit: int = 2000,
) -> list[CommitDocRow]:
    """Recent commit messages for a team's repos, newest first, for indexing."""
    rows = conn.execute(
        "SELECT c.sha, c.repo, c.author, c.message, c.committed_at "
        "FROM commits c JOIN repos r ON c.repo = r.repo "
        "WHERE r.team = ? AND c.committed_at >= ? "
        "ORDER BY c.committed_at DESC LIMIT ?",
        [team, since, limit],
    ).fetchall()
    return [CommitDocRow(*row) for row in rows]


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


# --- daily rollup sources ---------------------------------------------------


@dataclass(frozen=True, slots=True)
class DailyValueRow:
    """One (team, day) aggregate, before it is named and stored as a metric."""

    team: str
    day: date
    value: float


def get_daily_commit_counts(
    conn: duckdb.DuckDBPyConnection, since: date, until: date
) -> list[DailyValueRow]:
    """Commits per team per day over [since, until)."""
    rows = conn.execute(
        "SELECT r.team, CAST(c.committed_at AS DATE) AS day, count(*) "
        "FROM commits c JOIN repos r ON c.repo = r.repo "
        "WHERE r.team IS NOT NULL AND c.committed_at >= ? AND c.committed_at < ? "
        "GROUP BY 1, 2 ORDER BY 1, 2",
        [since, until],
    ).fetchall()
    return [DailyValueRow(team, day, float(value)) for team, day, value in rows]


def get_daily_push_counts(
    conn: duckdb.DuckDBPyConnection, since: date, until: date
) -> list[DailyValueRow]:
    """Pushes per team per day over [since, until)."""
    rows = conn.execute(
        "SELECT r.team, CAST(p.pushed_at AS DATE) AS day, count(*) "
        "FROM pushes p JOIN repos r ON p.repo = r.repo "
        "WHERE r.team IS NOT NULL AND p.pushed_at >= ? AND p.pushed_at < ? "
        "GROUP BY 1, 2 ORDER BY 1, 2",
        [since, until],
    ).fetchall()
    return [DailyValueRow(team, day, float(value)) for team, day, value in rows]


def get_daily_review_time_hours(
    conn: duckdb.DuckDBPyConnection, since: date, until: date
) -> list[DailyValueRow]:
    """Average hours-to-first-review per team per day, bucketed by open date.

    Only days where at least one PR was both opened and later reviewed produce
    a value: a day with no reviewed PRs is missing data, not a review time of
    zero, and filling it with zero would poison the baseline.
    """
    rows = conn.execute(
        "SELECT r.team, CAST(p.opened_at AS DATE) AS day, "
        "avg(date_diff('minute', p.opened_at, p.first_review_at) / 60.0) "
        "FROM pull_requests p JOIN repos r ON p.repo = r.repo "
        "WHERE r.team IS NOT NULL AND p.first_review_at IS NOT NULL "
        "AND p.opened_at >= ? AND p.opened_at < ? "
        "GROUP BY 1, 2 ORDER BY 1, 2",
        [since, until],
    ).fetchall()
    return [DailyValueRow(team, day, float(value)) for team, day, value in rows]


def get_active_days(
    conn: duckdb.DuckDBPyConnection, team: str, since: date, until: date
) -> list[date]:
    """Days in [since, until) on which the team's repos recorded any commit.

    Zero-filling the commit series needs a notion of "the team existed and did
    nothing" versus "we have no data yet", and the first commit we ever saw is
    the honest start of the series.
    """
    rows = conn.execute(
        "SELECT DISTINCT CAST(c.committed_at AS DATE) AS day "
        "FROM commits c JOIN repos r ON c.repo = r.repo "
        "WHERE r.team = ? AND c.committed_at >= ? AND c.committed_at < ? "
        "ORDER BY day",
        [team, since, until],
    ).fetchall()
    return [row[0] for row in rows]


# --- team member stats ------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MemberStatsRow:
    author: str
    commit_count: int
    linked_commit_count: int
    last_committed_at: datetime
    avg_review_hours: float | None


# A commit counts as "on goal" when it references tracked work: an issue or PR
# number, or a closing keyword. It is a proxy, but a checkable one, and it beats
# asking a language model to guess whether a commit matched the sprint.
_LINKED_COMMIT_PATTERN = r"(#[0-9]+)|(?i:\b(fix(es|ed)?|close[sd]?|resolve[sd]?)\b)"


def get_member_stats(
    conn: duckdb.DuckDBPyConnection, team: str, since: datetime
) -> list[MemberStatsRow]:
    """Per-author activity for a team since a cutoff, busiest first."""
    rows = conn.execute(
        """
        WITH commit_stats AS (
            SELECT c.author,
                   count(*) AS commit_count,
                   sum(CASE WHEN regexp_matches(c.message, ?) THEN 1 ELSE 0 END)
                       AS linked_commit_count,
                   max(c.committed_at) AS last_committed_at
            FROM commits c JOIN repos r ON c.repo = r.repo
            WHERE r.team = ? AND c.committed_at >= ?
            GROUP BY c.author
        ),
        review_stats AS (
            SELECT p.author,
                   avg(date_diff('minute', p.opened_at, p.first_review_at) / 60.0)
                       AS avg_review_hours
            FROM pull_requests p JOIN repos r ON p.repo = r.repo
            WHERE r.team = ? AND p.first_review_at IS NOT NULL
              AND p.opened_at >= ?
            GROUP BY p.author
        )
        SELECT c.author, c.commit_count, c.linked_commit_count,
               c.last_committed_at, rv.avg_review_hours
        FROM commit_stats c
        LEFT JOIN review_stats rv ON rv.author = c.author
        ORDER BY c.commit_count DESC, c.author
        """,
        [_LINKED_COMMIT_PATTERN, team, since, team, since],
    ).fetchall()
    return [
        MemberStatsRow(
            author=author,
            commit_count=int(commit_count),
            linked_commit_count=int(linked or 0),
            last_committed_at=last_committed_at,
            avg_review_hours=float(avg_review) if avg_review is not None else None,
        )
        for author, commit_count, linked, last_committed_at, avg_review in rows
    ]


# --- anomaly events + resolutions -------------------------------------------


@dataclass(frozen=True, slots=True)
class AnomalyEventRow:
    id: str
    team: str
    metric: str
    severity: str
    title: str
    description: str
    observed: float
    baseline: float
    z_score: float
    detected_at: datetime
    last_seen_at: datetime
    cleared_at: datetime | None
    notified_at: datetime | None


def anomaly_event_id(team: str, metric: str) -> str:
    """Stable key for an anomaly: one open event per team and metric."""
    return f"{team}:{metric}"


def upsert_anomaly_event(
    conn: duckdb.DuckDBPyConnection,
    *,
    team: str,
    metric: str,
    severity: str,
    title: str,
    description: str,
    observed: float,
    baseline: float,
    z_score: float,
    seen_at: datetime,
) -> str:
    """Record that an anomaly is currently firing.

    A row that was previously cleared is reopened: `detected_at` resets so the
    open-duration label stays meaningful for the next resolution.
    """
    event_id = anomaly_event_id(team, metric)
    conn.execute(
        "INSERT INTO anomaly_events "
        "(id, team, metric, severity, title, description, observed, baseline, "
        " z_score, detected_at, last_seen_at, cleared_at, notified_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL) "
        "ON CONFLICT (id) DO UPDATE SET "
        "severity = excluded.severity, title = excluded.title, "
        "description = excluded.description, observed = excluded.observed, "
        "baseline = excluded.baseline, z_score = excluded.z_score, "
        "last_seen_at = excluded.last_seen_at, "
        "detected_at = CASE WHEN anomaly_events.cleared_at IS NULL "
        "                   THEN anomaly_events.detected_at "
        "                   ELSE excluded.detected_at END, "
        "cleared_at = NULL",
        [
            event_id,
            team,
            metric,
            severity,
            title,
            description,
            observed,
            baseline,
            z_score,
            seen_at,
            seen_at,
        ],
    )
    return event_id


def get_open_anomaly_events(
    conn: duckdb.DuckDBPyConnection, team: str | None = None
) -> list[AnomalyEventRow]:
    """Anomalies that have not been cleared, worst-recent first."""
    rows = conn.execute(
        "SELECT id, team, metric, severity, title, description, observed, "
        "baseline, z_score, detected_at, last_seen_at, cleared_at, notified_at "
        "FROM anomaly_events "
        "WHERE cleared_at IS NULL AND (? IS NULL OR team = ?) "
        "ORDER BY detected_at DESC",
        [team, team],
    ).fetchall()
    return [AnomalyEventRow(*row) for row in rows]


def get_unnotified_events(
    conn: duckdb.DuckDBPyConnection, severities: Sequence[str]
) -> list[AnomalyEventRow]:
    """Open anomalies at the given severities that have never been alerted on."""
    if not severities:
        return []
    placeholders = ", ".join("?" for _ in severities)
    rows = conn.execute(
        "SELECT id, team, metric, severity, title, description, observed, "
        "baseline, z_score, detected_at, last_seen_at, cleared_at, notified_at "
        "FROM anomaly_events "
        "WHERE cleared_at IS NULL AND notified_at IS NULL "
        f"AND severity IN ({placeholders}) "
        "ORDER BY detected_at",
        list(severities),
    ).fetchall()
    return [AnomalyEventRow(*row) for row in rows]


def mark_events_notified(
    conn: duckdb.DuckDBPyConnection, event_ids: Sequence[str], notified_at: datetime
) -> None:
    if not event_ids:
        return
    conn.executemany(
        "UPDATE anomaly_events SET notified_at = ? WHERE id = ?",
        [(notified_at, event_id) for event_id in event_ids],
    )


def clear_anomaly_event(
    conn: duckdb.DuckDBPyConnection, event_id: str, cleared_at: datetime
) -> None:
    conn.execute(
        "UPDATE anomaly_events SET cleared_at = ? WHERE id = ? AND cleared_at IS NULL",
        [cleared_at, event_id],
    )


def insert_resolution(
    conn: duckdb.DuckDBPyConnection,
    *,
    anomaly_id: str,
    team: str,
    metric: str,
    severity: str,
    action: str,
    outcome: str,
    detected_at: datetime,
    resolved_at: datetime,
) -> None:
    """Write a labeled example: this anomaly closed, after this long."""
    open_days = (resolved_at - detected_at).total_seconds() / 86400.0
    conn.execute(
        "INSERT INTO resolutions "
        "(anomaly_id, team, metric, severity, action, outcome, detected_at, "
        " resolved_at, open_days) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            anomaly_id,
            team,
            metric,
            severity,
            action,
            outcome,
            detected_at,
            resolved_at,
            open_days,
        ],
    )


@dataclass(frozen=True, slots=True)
class ResolutionRow:
    anomaly_id: str
    team: str
    metric: str
    severity: str
    action: str
    outcome: str
    detected_at: datetime
    resolved_at: datetime
    open_days: float


def list_resolutions(
    conn: duckdb.DuckDBPyConnection, team: str | None = None
) -> list[ResolutionRow]:
    rows = conn.execute(
        "SELECT anomaly_id, team, metric, severity, action, outcome, "
        "detected_at, resolved_at, open_days FROM resolutions "
        "WHERE (? IS NULL OR team = ?) ORDER BY resolved_at DESC",
        [team, team],
    ).fetchall()
    return [ResolutionRow(*row) for row in rows]


# --- cached Phi-4 summaries -------------------------------------------------


@dataclass(frozen=True, slots=True)
class SummaryRow:
    team: str
    summary: str
    root_cause: str
    remediation_steps: str  # JSON-encoded list[str]
    verify_signal: str
    on_goal_score: float
    generated_at: datetime


def upsert_summary(conn: duckdb.DuckDBPyConnection, row: SummaryRow) -> None:
    conn.execute(
        "INSERT INTO summaries (team, summary, root_cause, remediation_steps, "
        "verify_signal, on_goal_score, generated_at) VALUES (?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT (team) DO UPDATE SET summary = excluded.summary, "
        "root_cause = excluded.root_cause, "
        "remediation_steps = excluded.remediation_steps, "
        "verify_signal = excluded.verify_signal, "
        "on_goal_score = excluded.on_goal_score, "
        "generated_at = excluded.generated_at",
        [
            row.team,
            row.summary,
            row.root_cause,
            row.remediation_steps,
            row.verify_signal,
            row.on_goal_score,
            row.generated_at,
        ],
    )


def get_summary(conn: duckdb.DuckDBPyConnection, team: str) -> SummaryRow | None:
    row = conn.execute(
        "SELECT team, summary, root_cause, remediation_steps, verify_signal, "
        "on_goal_score, generated_at FROM summaries WHERE team = ?",
        [team],
    ).fetchone()
    return SummaryRow(*row) if row else None


# --- operator settings ------------------------------------------------------

SETTING_DATA_SOURCE = "data_source"
SETTING_GITHUB_REPOS = "github_repos"

DATA_SOURCE_DEMO = "demo"
DATA_SOURCE_GITHUB = "github"


def set_setting(
    conn: duckdb.DuckDBPyConnection, key: str, value: str, updated_at: datetime
) -> None:
    conn.execute(
        "INSERT INTO app_settings (key, value, updated_at) VALUES (?, ?, ?) "
        "ON CONFLICT (key) DO UPDATE SET value = excluded.value, "
        "updated_at = excluded.updated_at",
        [key, value, updated_at],
    )


def get_setting(
    conn: duckdb.DuckDBPyConnection, key: str, default: str | None = None
) -> str | None:
    row = conn.execute(
        "SELECT value FROM app_settings WHERE key = ?", [key]
    ).fetchone()
    return row[0] if row else default


def get_all_settings(conn: duckdb.DuckDBPyConnection) -> dict[str, str]:
    rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
    return dict(rows)
