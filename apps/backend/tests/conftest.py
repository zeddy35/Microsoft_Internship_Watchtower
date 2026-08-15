"""Shared fixtures: an in-memory DuckDB, seeded activity, and a wired TestClient.

Nothing here touches the network, the filesystem, or a language model. The API
tests run against the same seeded database as the unit tests and a fake Phi-4
client, so a failure points at Watchtower's own logic rather than at whether
Foundry Local happened to be running.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

import duckdb
import pytest

# Settings are read at import time by pydantic-settings, so the environment has
# to look complete before anything under `app.` is imported.
os.environ.setdefault("LLM_BASE_URL", "http://localhost:5272/v1")
os.environ.setdefault("LLM_API_KEY", "test")
os.environ.setdefault("LLM_MODEL", "phi-4")
os.environ.setdefault("EMBEDDING_MODEL", "BAAI/bge-m3")
os.environ.setdefault("DUCKDB_PATH", "./data/test-watchtower.duckdb")
os.environ.setdefault("CHROMA_PATH", "./data/test-chroma")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
os.environ.setdefault("GITHUB_REPOS", "microsoft/vscode")
os.environ.setdefault("TEAMS_WEBHOOK_URL", "")
os.environ.setdefault("SCHEDULER_ENABLED", "false")

from app.core.db import (
    CommitRow,
    PullRequestRow,
    PushRow,
    init_schema,
    insert_commits,
    insert_pushes,
    upsert_pull_requests,
    upsert_repo,
)

TEAM = "vscode"
REPO = "microsoft/vscode"

# A fixed clock keeps every assertion about baselines and windows reproducible.
NOW = datetime(2026, 8, 15, 12, 0, 0)

BASELINE_DAYS = 45
QUIET_DAYS = 3
BASELINE_COMMITS_PER_DAY = 6


@pytest.fixture
def conn() -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect(":memory:")
    init_schema(connection)
    yield connection
    connection.close()


def seed_activity(
    connection: duckdb.DuckDBPyConnection,
    *,
    now: datetime = NOW,
    quiet_days: int = QUIET_DAYS,
    authors: tuple[str, ...] = ("elena", "raj", "wei"),
) -> None:
    """A team with a healthy history that goes quiet in the last few days.

    Ownership is deliberately lopsided (the first author writes most of the
    commits) so the bus-factor assertions have something to find.
    """
    upsert_repo(connection, REPO, team=TEAM)

    commits: list[CommitRow] = []
    pushes: list[PushRow] = []
    # Activity stops `quiet_days` before now: the last commit lands on
    # now - quiet_days, leaving exactly that many silent days at the end.
    for day_offset in range(BASELINE_DAYS, quiet_days - 1, -1):
        day = now - timedelta(days=day_offset)
        # A little day-to-day variation so stddev is non-zero and the z-score
        # is defined, but small enough that a drop to zero is unmistakable.
        count = BASELINE_COMMITS_PER_DAY + (day_offset % 3) - 1
        for index in range(count):
            author = authors[0] if index % 3 != 2 else authors[index % len(authors)]
            sha = f"sha-{day_offset}-{index}"
            commits.append(
                CommitRow(
                    sha=sha,
                    repo=REPO,
                    author=author,
                    message=(
                        f"Fix routing edge case #{100 + index}"
                        if index % 2 == 0
                        else "Refactor internals"
                    ),
                    additions=10 + index,
                    deletions=index,
                    committed_at=day.replace(hour=10, minute=0, second=0),
                )
            )
        pushes.append(
            PushRow(
                repo=REPO,
                author=authors[0],
                ref="refs/heads/main",
                pushed_at=day.replace(hour=11, minute=0, second=0),
            )
        )

    insert_commits(connection, commits)
    insert_pushes(connection, pushes)

    # Reviewed PRs: fast for most of the window, then a stale one still open.
    prs: list[PullRequestRow] = []
    for index, day_offset in enumerate(range(BASELINE_DAYS, quiet_days, -2)):
        opened = (now - timedelta(days=day_offset)).replace(hour=9)
        prs.append(
            PullRequestRow(
                id=1000 + index,
                repo=REPO,
                author=authors[index % len(authors)],
                opened_at=opened,
                first_review_at=opened + timedelta(hours=6),
                merged_at=opened + timedelta(days=1),
                state="closed",
            )
        )
    prs.append(
        PullRequestRow(
            id=2001,
            repo=REPO,
            author=authors[1],
            opened_at=now - timedelta(days=21),
            first_review_at=None,
            merged_at=None,
            state="open",
        )
    )
    upsert_pull_requests(connection, prs)


@pytest.fixture
def seeded(conn: duckdb.DuckDBPyConnection) -> duckdb.DuckDBPyConnection:
    seed_activity(conn)
    return conn
