"""Team endpoints: the data behind the overview cards and the drill-down."""

from __future__ import annotations

import logging
from collections.abc import Iterator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.ai.resolver import stream_answer
from app.anomaly.engine import detect_team_anomalies
from app.api import services
from app.api.deps import DbConn, TeamName
from app.core.schemas import (
    AnomalyOut,
    AskRequest,
    BusFactorAreaOut,
    TeamMetricsOut,
    TeamOut,
    TeamSummaryOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=list[TeamOut])
def list_teams_route(conn: DbConn) -> list[TeamOut]:
    return services.build_teams(conn)


@router.get("/{team_id}", response_model=TeamOut)
def get_team_route(conn: DbConn, team: TeamName) -> TeamOut:
    return services.build_team(conn, team)


@router.get("/{team_id}/metrics", response_model=TeamMetricsOut)
def get_team_metrics_route(conn: DbConn, team: TeamName) -> TeamMetricsOut:
    return services.build_team_metrics(conn, team)


@router.get("/{team_id}/anomalies", response_model=list[AnomalyOut])
def get_team_anomalies_route(conn: DbConn, team: TeamName) -> list[AnomalyOut]:
    return services.build_anomalies(conn, team)


@router.get("/{team_id}/bus-factor", response_model=list[BusFactorAreaOut])
def get_team_bus_factor_route(conn: DbConn, team: TeamName) -> list[BusFactorAreaOut]:
    return services.build_team(conn, team).bus_factor_areas


@router.get("/{team_id}/summary", response_model=TeamSummaryOut)
def get_team_summary_route(conn: DbConn, team: TeamName) -> TeamSummaryOut:
    summary = services.build_summary(conn, team)
    if summary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No Phi-4 summary has been generated for this team yet. "
                "Run POST /admin/refresh with the local model running."
            ),
        )
    return summary


@router.post("/{team_id}/ask")
def ask_team_route(
    conn: DbConn, team: TeamName, payload: AskRequest
) -> StreamingResponse:
    """Stream a Phi-4 answer about one team, grounded in its current evidence.

    Plain `text/plain` chunks rather than SSE: the client renders the tokens as
    they arrive and there is no event taxonomy to justify the extra framing.
    """
    anomalies = detect_team_anomalies(conn, team)

    def token_stream() -> Iterator[str]:
        try:
            yield from stream_answer(team, payload.question, anomalies)
        except Exception:
            logger.exception("Streaming answer failed for %s", team)
            yield "\n\n[Watchtower could not reach the local model.]"

    return StreamingResponse(
        token_stream(),
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )
