"""Operational endpoints: refresh, settings, demo data, the resolution log.

`POST /admin/refresh` exists so a demo never has to wait out the scheduler
interval, and so the pipeline can be exercised end to end from the browser.
`POST /admin/seed-demo` fills an empty database with a fabricated organisation
so every screen has something to show without a GitHub token or a local model.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DbConn
from app.config import get_settings
from app.core.clock import utcnow
from app.core.db import (
    DATA_SOURCE_GITHUB,
    SETTING_DATA_SOURCE,
    SETTING_GITHUB_REPOS,
    get_setting,
    list_resolutions,
    set_setting,
)
from app.core.schemas import (
    ApiModel,
    RefreshResult,
    SeedResultOut,
    SettingsOut,
    SettingsUpdate,
)
from app.jobs import run_anomaly_pass, run_refresh
from app.metrics.rollup import rollup_metrics
from app.seed.demo import clear_demo_data, seed_demo_data

router = APIRouter(prefix="/admin", tags=["admin"])


class ResolutionOut(ApiModel):
    anomaly_id: str
    team_id: str
    metric: str
    severity: str
    action: str
    outcome: str
    detected_at: str
    resolved_at: str
    open_days: float


# --- refresh ----------------------------------------------------------------


@router.post("/refresh", response_model=RefreshResult)
async def refresh_route(
    conn: DbConn,
    collect: bool = Query(default=True, description="Pull fresh data from GitHub"),
    resolve: bool = Query(default=True, description="Regenerate Phi-4 summaries"),
    notify: bool = Query(default=True, description="Send Teams alerts"),
) -> RefreshResult:
    return await run_refresh(conn, collect=collect, resolve=resolve, notify=notify)


# --- settings ---------------------------------------------------------------


def _current_repos(conn: DbConn) -> list[str]:
    """Repos from the settings table, falling back to the .env default."""
    stored = get_setting(conn, SETTING_GITHUB_REPOS)
    if stored is not None:
        return [repo.strip() for repo in stored.split(",") if repo.strip()]
    return list(get_settings().GITHUB_REPOS)


@router.get("/settings", response_model=SettingsOut)
def get_settings_route(conn: DbConn) -> SettingsOut:
    settings = get_settings()
    return SettingsOut(
        data_source=get_setting(conn, SETTING_DATA_SOURCE, DATA_SOURCE_GITHUB),  # type: ignore[arg-type]
        github_repos=_current_repos(conn),
        github_token_configured=bool(settings.GITHUB_TOKEN),
        teams_webhook_configured=bool(settings.TEAMS_WEBHOOK_URL),
        scheduler_enabled=settings.SCHEDULER_ENABLED,
        refresh_interval_minutes=settings.REFRESH_INTERVAL_MINUTES,
        duckdb_path=str(settings.DUCKDB_PATH),
        llm_base_url=settings.LLM_BASE_URL,
        llm_model=settings.LLM_MODEL,
    )


@router.put("/settings", response_model=SettingsOut)
def update_settings_route(conn: DbConn, payload: SettingsUpdate) -> SettingsOut:
    """Update the two things a user may change: data source and watched repos.

    Deliberately not writable from here: the GitHub token, the webhook URL, and
    anything else that is a secret or a deployment concern. Those stay in .env.
    """
    now = utcnow()
    if payload.data_source is not None:
        set_setting(conn, SETTING_DATA_SOURCE, payload.data_source, now)
    if payload.github_repos is not None:
        cleaned = ",".join(
            repo.strip() for repo in payload.github_repos if repo.strip()
        )
        set_setting(conn, SETTING_GITHUB_REPOS, cleaned, now)
    return get_settings_route(conn)


# --- demo data --------------------------------------------------------------


@router.post("/seed-demo", response_model=SeedResultOut)
def seed_demo_route(
    conn: DbConn,
    reset: bool = Query(
        default=True, description="Wipe collected data before seeding"
    ),
) -> SeedResultOut:
    """Fill every table with the fabricated three-team organisation.

    The anomalies are not written by hand: the seeded activity goes through the
    real rollup and the real engine, so the demo shows what Watchtower actually
    detects rather than a picture of it.
    """
    if reset:
        clear_demo_data(conn)

    result = seed_demo_data(conn)
    rollup = rollup_metrics(conn)
    anomalies = run_anomaly_pass(conn)

    return SeedResultOut(
        teams=result.teams,
        commits=result.commits,
        pushes=result.pushes,
        pull_requests=result.pull_requests,
        resolutions=result.resolutions,
        summaries=result.summaries,
        metric_rows=rollup.rows_written,
        anomalies_open=anomalies.open_count,
    )


@router.post("/clear", response_model=SettingsOut)
def clear_route(conn: DbConn) -> SettingsOut:
    """Empty every data table, leaving configuration in place."""
    clear_demo_data(conn)
    set_setting(conn, SETTING_DATA_SOURCE, DATA_SOURCE_GITHUB, utcnow())
    return get_settings_route(conn)


# --- resolution log ---------------------------------------------------------


@router.get("/resolutions", response_model=list[ResolutionOut])
def list_resolutions_route(
    conn: DbConn, team: str | None = None
) -> list[ResolutionOut]:
    """The labeled outcome log the predictive layer will train on."""
    return [
        ResolutionOut(
            anomaly_id=row.anomaly_id,
            team_id=row.team,
            metric=row.metric,
            severity=row.severity,
            action=row.action,
            outcome=row.outcome,
            detected_at=row.detected_at.isoformat(),
            resolved_at=row.resolved_at.isoformat(),
            open_days=round(row.open_days, 2),
        )
        for row in list_resolutions(conn, team)
    ]
