"""Cross-team anomaly feed, for the overview table and the anomalies page."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api import services
from app.api.deps import DbConn
from app.core.schemas import AnomalyOut, AnomalySeverity

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("", response_model=list[AnomalyOut])
def list_anomalies_route(
    conn: DbConn,
    severity: AnomalySeverity | None = Query(
        default=None, description="Only return anomalies at this severity"
    ),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[AnomalyOut]:
    anomalies = services.build_anomalies(conn)
    if severity is not None:
        anomalies = [a for a in anomalies if a.severity == severity]
    return anomalies[:limit]
