"""GitHub collector: pulls commits, pushes, and pull requests for each
configured repo into DuckDB, incrementally since the last stored timestamp.

Uses httpx directly (async) rather than PyGithub, since PyGithub's client is
synchronous and would block the event loop inside an async collect_all().

A few API shape gotchas worth knowing:
- GitHub has no first-class "push" resource, so pushes are approximated from
  the Events API's PushEvent entries (capped at ~90 days / 300 events per
  GitHub's own retention, which is fine for a rolling-baseline demo).
- Per-commit additions/deletions and a PR's first-review timestamp each cost
  one extra API call (the list endpoints don't include them), so both are
  capped per sync (_MAX_COMMIT_STATS_PER_SYNC / _MAX_PR_REVIEWS_PER_SYNC) to
  stay well within rate limits against large public repos like vscode.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.config import get_settings
from app.core.db import (
    CommitRow,
    PullRequestRow,
    PushRow,
    get_connection,
    get_repo_last_synced_at,
    insert_commits,
    insert_pushes,
    update_repo_synced_at,
    upsert_pull_requests,
    upsert_repo,
)

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
DEFAULT_LOOKBACK_DAYS = 30
_MAX_COMMIT_STATS_PER_SYNC = 20
_MAX_PR_REVIEWS_PER_SYNC = 30
_PER_PAGE = 100
_MAX_RETRIES = 5


def derive_team_name(repo: str) -> str:
    """Default team-per-repo mapping for the demo: the repo name without the owner."""
    return repo.split("/", 1)[1] if "/" in repo else repo


def _parse_github_timestamp(value: str) -> datetime:
    """GitHub timestamps are always UTC ("...Z"); store naive-UTC to match DuckDB TIMESTAMP."""
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC).replace(tzinfo=None)


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _make_client(token: str) -> httpx.AsyncClient:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return httpx.AsyncClient(base_url=GITHUB_API_BASE, headers=headers, timeout=30.0)


async def _request_with_backoff(
    client: httpx.AsyncClient, method: str, url: str, **kwargs: Any
) -> httpx.Response:
    response: httpx.Response | None = None
    for attempt in range(_MAX_RETRIES):
        response = await client.request(method, url, **kwargs)

        if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
            reset_at = int(response.headers.get("X-RateLimit-Reset", "0"))
            wait_seconds = max(1, reset_at - int(datetime.now(UTC).timestamp())) + 1
            logger.warning("GitHub rate limit hit, sleeping %ss", wait_seconds)
            await asyncio.sleep(wait_seconds)
            continue

        if response.status_code >= 500:
            wait_seconds = 2**attempt
            logger.warning(
                "GitHub API %s on %s, retrying in %ss", response.status_code, url, wait_seconds
            )
            await asyncio.sleep(wait_seconds)
            continue

        response.raise_for_status()
        return response

    assert response is not None
    response.raise_for_status()
    return response


async def _paginate(
    client: httpx.AsyncClient, url: str, params: dict[str, Any]
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    next_url: str | None = url
    next_params: dict[str, Any] | None = params

    while next_url:
        response = await _request_with_backoff(client, "GET", next_url, params=next_params)
        items.extend(response.json())
        next_url = response.links.get("next", {}).get("url")
        next_params = None  # the next-page URL already carries its own query string

    return items


async def _collect_commits(
    client: httpx.AsyncClient,
    conn: Any,
    repo: str,
    since: datetime,
) -> None:
    items = await _paginate(
        client,
        f"/repos/{repo}/commits",
        {"since": since.isoformat() + "Z", "per_page": _PER_PAGE},
    )

    rows: list[CommitRow] = []
    for index, item in enumerate(items):
        sha = item["sha"]
        commit = item["commit"]
        author_login = (item.get("author") or {}).get("login") or commit["author"]["name"]
        committed_at = _parse_github_timestamp(commit["committer"]["date"])

        additions = deletions = 0
        if index < _MAX_COMMIT_STATS_PER_SYNC:
            detail = await _request_with_backoff(client, "GET", f"/repos/{repo}/commits/{sha}")
            stats = detail.json().get("stats", {})
            additions, deletions = stats.get("additions", 0), stats.get("deletions", 0)

        rows.append(
            CommitRow(
                sha=sha,
                repo=repo,
                author=author_login,
                message=commit["message"],
                additions=additions,
                deletions=deletions,
                committed_at=committed_at,
            )
        )

    insert_commits(conn, rows)
    logger.info("Collected %d commits for %s", len(rows), repo)


async def _collect_pushes(
    client: httpx.AsyncClient,
    conn: Any,
    repo: str,
    since: datetime,
) -> None:
    items = await _paginate(client, f"/repos/{repo}/events", {"per_page": _PER_PAGE})

    rows: list[PushRow] = []
    for item in items:
        if item["type"] != "PushEvent":
            continue
        pushed_at = _parse_github_timestamp(item["created_at"])
        if pushed_at < since:
            continue
        rows.append(
            PushRow(
                repo=repo,
                author=item["actor"]["login"],
                ref=item["payload"].get("ref", ""),
                pushed_at=pushed_at,
            )
        )

    insert_pushes(conn, rows)
    logger.info("Collected %d pushes for %s", len(rows), repo)


async def _collect_pull_requests(
    client: httpx.AsyncClient,
    conn: Any,
    repo: str,
    since: datetime,
) -> None:
    items = await _paginate(
        client,
        f"/repos/{repo}/pulls",
        {"state": "all", "sort": "updated", "direction": "desc", "per_page": _PER_PAGE},
    )

    rows: list[PullRequestRow] = []
    reviews_fetched = 0
    for item in items:
        updated_at = _parse_github_timestamp(item["updated_at"])
        if updated_at < since:
            # Sorted by updated desc: everything after this point is older still.
            break

        opened_at = _parse_github_timestamp(item["created_at"])
        merged_at = _parse_github_timestamp(item["merged_at"]) if item.get("merged_at") else None
        state = "merged" if merged_at else item["state"]

        first_review_at: datetime | None = None
        if reviews_fetched < _MAX_PR_REVIEWS_PER_SYNC:
            reviews = await _request_with_backoff(
                client, "GET", f"/repos/{repo}/pulls/{item['number']}/reviews"
            )
            submitted_ats = [r["submitted_at"] for r in reviews.json() if r.get("submitted_at")]
            if submitted_ats:
                first_review_at = _parse_github_timestamp(min(submitted_ats))
            reviews_fetched += 1

        rows.append(
            PullRequestRow(
                id=item["id"],
                repo=repo,
                author=item["user"]["login"],
                opened_at=opened_at,
                first_review_at=first_review_at,
                merged_at=merged_at,
                state=state,
            )
        )

    upsert_pull_requests(conn, rows)
    logger.info("Collected %d pull requests for %s", len(rows), repo)


async def collect_repo(client: httpx.AsyncClient, conn: Any, repo: str) -> None:
    """Sync one repo's commits, pushes, and pull requests since its last sync."""
    upsert_repo(conn, repo, team=derive_team_name(repo))
    since = get_repo_last_synced_at(conn, repo) or (
        _utcnow() - timedelta(days=DEFAULT_LOOKBACK_DAYS)
    )

    await _collect_commits(client, conn, repo, since)
    await _collect_pushes(client, conn, repo, since)
    await _collect_pull_requests(client, conn, repo, since)

    update_repo_synced_at(conn, repo, _utcnow())


async def collect_all() -> None:
    """Sync every repo in settings.GITHUB_REPOS. Logs and continues on per-repo failure."""
    settings = get_settings()
    # Own cursor: collection runs alongside live requests and the scheduler,
    # and a DuckDB connection must not be shared across threads.
    conn = get_connection().cursor()

    async with _make_client(settings.GITHUB_TOKEN) as client:
        for repo in settings.GITHUB_REPOS:
            try:
                await collect_repo(client, conn, repo)
            except Exception:
                logger.exception("Failed to collect %s", repo)
