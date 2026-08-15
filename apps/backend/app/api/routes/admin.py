"""Operational endpoints: force a refresh, inspect the resolution log.

`POST /admin/refresh` exists so a demo never has to wait out the scheduler
interval, and so the pipeline can be exercised end to end from the browser.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DbConn
from app.core.db import list_resolutions
from app.core.schemas import ApiModel, RefreshResult
from app.jobs import run_refresh

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


@router.post("/refresh", response_model=RefreshResult)
async def refresh_route(
    conn: DbConn,
    collect: bool = Query(default=True, description="Pull fresh data from GitHub"),
    resolve: bool = Query(default=True, description="Regenerate Phi-4 summaries"),
    notify: bool = Query(default=True, description="Send Teams alerts"),
) -> RefreshResult:
    return await run_refresh(conn, collect=collect, resolve=resolve, notify=notify)


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
