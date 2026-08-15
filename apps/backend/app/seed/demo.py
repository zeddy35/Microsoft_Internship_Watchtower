"""A synthetic organisation, so every screen has something honest to show.

Watchtower's whole story is a loop - detect, explain, then check whether the
advice worked - and on an empty database none of it is visible: the Phi-4 card
404s, the resolutions log is blank, and the overview is three empty states.
This module fabricates three teams with deliberately different health so the
loop can be demonstrated end to end without a GitHub token or a local model.

Two rules keep it honest:

- Every row is generated from a fixed seed, so the demo looks the same on
  every machine and a screenshot taken today still matches next week.
- The data is *labelled* as fabricated. `data_source` is set to "demo" and the
  UI says so, because a dashboard that cannot tell you where its numbers came
  from is worse than an empty one.

The anomalies are not hand-written: the seeded activity is fed through the
real rollup and the real anomaly engine, so what the demo shows is what the
engine actually detects. Only the Phi-4 summaries are canned, because the
model runs locally and may not be up.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import datetime, timedelta

import duckdb

from app.core.clock import utcnow
from app.core.db import (
    CommitRow,
    PullRequestRow,
    PushRow,
    SummaryRow,
    anomaly_event_id,
    insert_commits,
    insert_pushes,
    insert_resolution,
    set_setting,
    upsert_pull_requests,
    upsert_repo,
    upsert_summary,
)

SEED = 20260815
HISTORY_DAYS = 90

# Commit subjects, so the vector store and the on-goal heuristic have realistic
# text to chew on. Roughly half reference tracked work, which is what the
# "on goal" metric counts.
COMMIT_SUBJECTS = [
    "Fix connection reset on idle peers #{n}",
    "Add retry budget to the control plane #{n}",
    "Refactor the telemetry batcher",
    "Tidy up logging in the ingest path",
    "Close race in the session cache #{n}",
    "Bump dependency versions",
    "Resolve flaky integration test #{n}",
    "Document the failover runbook",
    "Fix off-by-one in the retry backoff #{n}",
    "Simplify config parsing",
]


@dataclass(frozen=True, slots=True)
class TeamProfile:
    """One synthetic team and the shape of the story it tells."""

    repo: str
    team: str
    authors: tuple[str, ...]
    # Commits per day before anything goes wrong.
    baseline_commits: int
    # Multiplier applied over the last `slump_days` days: 0.0 is a full stop.
    slump_factor: float
    slump_days: int
    # Hours from opening a PR to its first review, before and during the slump.
    review_hours: float
    review_hours_recent: float
    # Share of the team's commits written by its first author.
    top_owner_share: float
    stale_prs: int


PROFILES: tuple[TeamProfile, ...] = (
    # Critical: work stopped, reviews piled up, one person owns everything.
    TeamProfile(
        repo="microsoft/azure-core-networking",
        team="Azure Core Networking",
        authors=("epetrova", "rmalhotra", "wchen", "pnair", "mjohnson"),
        baseline_commits=8,
        slump_factor=0.1,
        slump_days=5,
        review_hours=9.0,
        review_hours_recent=96.0,
        top_owner_share=0.78,
        stale_prs=2,
    ),
    # At risk: a noticeable dip, reviews slower, ownership concentrated.
    TeamProfile(
        repo="microsoft/fabric-data-plane",
        team="Fabric Data Plane",
        authors=("skowalski", "achen", "dmartinez", "yfujita"),
        baseline_commits=6,
        slump_factor=0.55,
        slump_days=6,
        review_hours=11.0,
        review_hours_recent=30.0,
        top_owner_share=0.58,
        stale_prs=1,
    ),
    # Healthy: steady cadence, quick reviews, work spread across the team.
    TeamProfile(
        repo="microsoft/m365-copilot-extensibility",
        team="M365 Copilot Extensibility",
        authors=("lbergstrom", "kadeyemi", "tnakamura", "gosullivan", "hschmidt"),
        baseline_commits=7,
        slump_factor=1.0,
        slump_days=0,
        review_hours=7.0,
        review_hours_recent=6.5,
        top_owner_share=0.34,
        stale_prs=0,
    ),
)

# Written in the resolver's voice and stored as if a pass had produced them,
# so the summary card and the weekly digest have something to render when no
# local model is running. Regenerating them for real is one /admin/refresh.
SUMMARIES: dict[str, tuple[str, str, list[str], str, float]] = {
    "Azure Core Networking": (
        "Commit and push volume have effectively stopped over the last five days "
        "while time-to-first-review climbed past four days, which points at a "
        "review bottleneck rather than a drop in workload. Two pull requests have "
        "been open more than a week, and 78% of recent changes come from a single "
        "engineer, so the queue has nowhere else to go.",
        "A single reviewer is the bottleneck, and ownership concentration means "
        "no one else can clear the queue.",
        [
            "Rebalance the review queue: assign the two stale PRs to a second reviewer today",
            "Pair a second engineer onto the peering configuration area",
            "Split the largest open PR so it can be reviewed incrementally",
        ],
        "Time-to-first-review back under 24 hours for three consecutive days",
        41.0,
    ),
    "Fabric Data Plane": (
        "Commit volume is down about 45% against the 28-day baseline and reviews "
        "now take roughly a day and a half, up from half a day. The team is still "
        "shipping, but the trend has been consistently downward for a week and one "
        "pull request has gone stale.",
        "Review latency is creeping up as work concentrates on fewer contributors.",
        [
            "Clear the stale pull request before it blocks the next change",
            "Set a same-day first-review expectation for the coming sprint",
        ],
        "Commit volume back within 15% of the 28-day baseline",
        63.0,
    ),
    "M365 Copilot Extensibility": (
        "Cadence is steady, reviews land within a working day, and ownership is "
        "spread across five contributors with no area above 35%. Nothing here "
        "needs attention this week.",
        "No anomaly detected; the team is inside its baseline on every tracked metric.",
        [
            "Keep the current review rotation",
        ],
        "Commit volume staying within 15% of baseline",
        81.0,
    ),
}

# Anomalies that fired and then cleared. These are the loop's output: what was
# recommended, and how long the problem stayed open. The predictive layer (P1)
# trains on exactly this table.
CLOSED_ANOMALIES: tuple[tuple[str, str, str, str, int], ...] = (
    (
        "Azure Core Networking",
        "review_time_hours",
        "critical",
        "Rebalance the review queue across the team",
        9,
    ),
    (
        "Azure Core Networking",
        "commits_per_day",
        "warning",
        "Split the migration work into reviewable chunks",
        4,
    ),
    (
        "Fabric Data Plane",
        "pushes_per_day",
        "warning",
        "Re-enable the nightly integration branch",
        6,
    ),
    (
        "Fabric Data Plane",
        "stale_prs",
        "warning",
        "Assign a backup reviewer for the ingest area",
        3,
    ),
    (
        "M365 Copilot Extensibility",
        "commits_per_day",
        "info",
        "No action needed; the dip was a public holiday",
        2,
    ),
)


@dataclass(frozen=True, slots=True)
class SeedResult:
    teams: int
    commits: int
    pushes: int
    pull_requests: int
    resolutions: int
    summaries: int


def _weighted_author(rng: random.Random, profile: TeamProfile) -> str:
    """Pick an author, over-weighting the first one to create bus-factor risk."""
    if rng.random() < profile.top_owner_share:
        return profile.authors[0]
    return rng.choice(profile.authors[1:])


def _commits_for_day(rng: random.Random, profile: TeamProfile, days_ago: int) -> int:
    """Daily commit count, with weekends quiet and a slump at the end."""
    base = profile.baseline_commits
    if days_ago < profile.slump_days:
        base = base * profile.slump_factor
    # A little noise so the series has a defined standard deviation; without it
    # the engine cannot compute a z-score at all.
    count = max(0, round(rng.gauss(base, max(base * 0.25, 0.8))))
    return count


def _is_weekend(day: datetime) -> bool:
    return day.weekday() >= 5


def clear_demo_data(conn: duckdb.DuckDBPyConnection) -> None:
    """Drop everything derived and collected, leaving the schema in place."""
    for table in (
        "resolutions",
        "anomaly_events",
        "summaries",
        "metrics_daily",
        "commits",
        "pushes",
        "pull_requests",
        "repos",
    ):
        conn.execute(f"DELETE FROM {table}")


def seed_demo_data(
    conn: duckdb.DuckDBPyConnection, now: datetime | None = None
) -> SeedResult:
    """Fill every table with a deterministic three-team organisation."""
    now = now or utcnow()
    rng = random.Random(SEED)

    commits: list[CommitRow] = []
    pushes: list[PushRow] = []
    pull_requests: list[PullRequestRow] = []
    pr_id = 4000

    for profile in PROFILES:
        upsert_repo(conn, profile.repo, team=profile.team)

        for days_ago in range(HISTORY_DAYS, -1, -1):
            day = now - timedelta(days=days_ago)
            if _is_weekend(day):
                continue

            count = _commits_for_day(rng, profile, days_ago)
            for index in range(count):
                author = _weighted_author(rng, profile)
                subject = rng.choice(COMMIT_SUBJECTS).replace(
                    "{n}", str(rng.randint(100, 9999))
                )
                commits.append(
                    CommitRow(
                        sha=f"{profile.team[:3].lower()}-{days_ago}-{index}",
                        repo=profile.repo,
                        author=author,
                        message=subject,
                        additions=rng.randint(3, 240),
                        deletions=rng.randint(0, 120),
                        committed_at=day.replace(
                            hour=rng.randint(8, 18), minute=rng.randint(0, 59), second=0,
                            microsecond=0,
                        ),
                    )
                )

            if count:
                pushes.append(
                    PushRow(
                        repo=profile.repo,
                        author=_weighted_author(rng, profile),
                        ref="refs/heads/main",
                        pushed_at=day.replace(
                            hour=rng.randint(9, 19), minute=0, second=0, microsecond=0
                        ),
                    )
                )

            # A reviewed pull request every few days.
            if days_ago % 3 == 0:
                opened = day.replace(hour=10, minute=0, second=0, microsecond=0)
                latency = (
                    profile.review_hours_recent
                    if days_ago < profile.slump_days
                    else profile.review_hours
                )
                latency = max(1.0, rng.gauss(latency, latency * 0.2))
                pr_id += 1
                pull_requests.append(
                    PullRequestRow(
                        id=pr_id,
                        repo=profile.repo,
                        author=_weighted_author(rng, profile),
                        opened_at=opened,
                        first_review_at=opened + timedelta(hours=latency),
                        merged_at=opened + timedelta(hours=latency + 6),
                        state="closed",
                    )
                )

        # Pull requests that were opened and then forgotten.
        for index in range(profile.stale_prs):
            pr_id += 1
            pull_requests.append(
                PullRequestRow(
                    id=pr_id,
                    repo=profile.repo,
                    author=profile.authors[index % len(profile.authors)],
                    opened_at=now - timedelta(days=11 + index * 7),
                    first_review_at=None,
                    merged_at=None,
                    state="open",
                )
            )

    insert_commits(conn, commits)
    insert_pushes(conn, pushes)
    upsert_pull_requests(conn, pull_requests)

    resolutions = _seed_resolutions(conn, now)
    summaries = _seed_summaries(conn, now)

    set_setting(conn, "data_source", "demo", now)

    return SeedResult(
        teams=len(PROFILES),
        commits=len(commits),
        pushes=len(pushes),
        pull_requests=len(pull_requests),
        resolutions=resolutions,
        summaries=summaries,
    )


def _seed_resolutions(conn: duckdb.DuckDBPyConnection, now: datetime) -> int:
    """Anomalies that fired weeks ago and have since cleared."""
    for index, (team, metric, severity, action, open_days) in enumerate(
        CLOSED_ANOMALIES
    ):
        detected_at = now - timedelta(days=14 + index * 5 + open_days)
        insert_resolution(
            conn,
            anomaly_id=anomaly_event_id(team, metric),
            team=team,
            metric=metric,
            severity=severity,
            action=action,
            outcome="cleared",
            detected_at=detected_at,
            resolved_at=detected_at + timedelta(days=open_days),
        )
    return len(CLOSED_ANOMALIES)


def _seed_summaries(conn: duckdb.DuckDBPyConnection, now: datetime) -> int:
    for team, (
        summary,
        root_cause,
        steps,
        verify_signal,
        on_goal,
    ) in SUMMARIES.items():
        upsert_summary(
            conn,
            SummaryRow(
                team=team,
                summary=summary,
                root_cause=root_cause,
                remediation_steps=json.dumps(steps),
                verify_signal=verify_signal,
                on_goal_score=on_goal,
                generated_at=now - timedelta(hours=3),
            ),
        )
    return len(SUMMARIES)
