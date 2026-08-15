"""API response models.

These are the contract with the frontend, so the field names are camelCase and
the literal unions match `apps/frontend/src/lib/types.ts` exactly. Keep the two
files in step: the frontend re-validates every response with zod, so a rename
here surfaces as a runtime parse error there rather than a silent undefined.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer
from pydantic.alias_generators import to_camel


def _utc_isoformat(value: datetime) -> str:
    """Serialize as an explicit UTC instant, e.g. 2026-08-15T12:00:00Z.

    DuckDB hands back naive datetimes that are UTC by convention. Emitting them
    unmarked would let the browser read them as local time, so the offset is
    made explicit here rather than trusted to the client.
    """
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


UtcDatetime = Annotated[datetime, PlainSerializer(_utc_isoformat, return_type=str)]

TeamStatus = Literal["healthy", "at-risk", "critical"]
MemberActivityStatus = Literal["active", "away", "offline"]
MetricDirection = Literal["up", "down", "flat"]
MetricTrend = Literal["good", "caution", "bad"]
RiskLevel = Literal["low", "medium", "high"]
AnomalySeverity = Literal["info", "warning", "critical"]


class ApiModel(BaseModel):
    """Serializes as camelCase, accepts either casing when constructed."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )


class TeamMemberOut(ApiModel):
    id: str
    name: str
    role: str
    initials: str = Field(min_length=1, max_length=3)
    commits_per_week: float = Field(ge=0)
    avg_review_time_days: float = Field(ge=0)
    on_goal_rate: float = Field(ge=0, le=100)
    activity_status: MemberActivityStatus


class BusFactorAreaOut(ApiModel):
    id: str
    area: str
    top_owner: str
    ownership_percent: float = Field(ge=0, le=100)
    risk_level: RiskLevel


class TeamOut(ApiModel):
    id: str
    name: str
    status: TeamStatus
    health_score: float = Field(ge=0, le=100)
    engineer_count: int = Field(ge=0)
    source: str
    members: list[TeamMemberOut] = Field(default_factory=list)
    bus_factor_areas: list[BusFactorAreaOut] = Field(default_factory=list)
    # Commits per day over the trailing fortnight, oldest first, for the
    # overview card's sparkline.
    activity: list[float] = Field(default_factory=list)


class MetricOut(ApiModel):
    id: str
    label: str
    unit: str
    value: float
    baseline: float
    delta: float
    direction: MetricDirection
    trend: MetricTrend


class ReviewTimePointOut(ApiModel):
    date: str
    review_time_days: float
    baseline_days: float


class TeamMetricsOut(ApiModel):
    """The drill-down's four KPI cards plus the review-time trend line."""

    metrics: list[MetricOut] = Field(default_factory=list)
    review_time_history: list[ReviewTimePointOut] = Field(default_factory=list)


class AnomalyOut(ApiModel):
    id: str
    team_id: str
    severity: AnomalySeverity
    title: str
    description: str
    detected_at: UtcDatetime


class TeamSummaryOut(ApiModel):
    id: str
    team_id: str
    model: Literal["Phi-4"] = "Phi-4"
    summary: str
    suggestions: list[str] = Field(min_length=1)
    generated_at: UtcDatetime


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class RefreshResult(ApiModel):
    collected: bool
    metric_rows: int
    teams: int
    anomalies_open: int
    resolutions_written: int
    summaries_written: int


class HealthResponse(BaseModel):
    status: str
