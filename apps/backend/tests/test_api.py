"""API tests: real routes, seeded in-memory DuckDB, no model and no network.

These also pin the contract the frontend's zod schemas expect - camelCase keys,
the exact literal unions - so a rename on either side fails here first.
"""

from __future__ import annotations

import json
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_db
from app.core.db import SummaryRow, upsert_summary
from app.jobs import run_anomaly_pass
from app.main import create_app
from app.metrics.rollup import rollup_metrics
from tests.conftest import NOW, TEAM

TEAM_ID = TEAM.lower()


@pytest.fixture
def client(seeded):
    """The app, pointed at the seeded database, with the scheduler disabled."""
    rollup_metrics(seeded, until=(NOW + timedelta(days=1)).date())
    run_anomaly_pass(seeded, now=NOW)

    app = create_app()
    app.dependency_overrides[get_db] = lambda: seeded
    with TestClient(app) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_teams_returns_camel_case_fields(client):
    response = client.get("/teams")
    assert response.status_code == 200

    teams = response.json()
    assert len(teams) == 1
    team = teams[0]
    assert team["id"] == TEAM_ID
    assert {
        "id",
        "name",
        "status",
        "healthScore",
        "engineerCount",
        "source",
        "members",
        "busFactorAreas",
    } <= set(team)
    assert team["status"] in {"healthy", "at-risk", "critical"}
    assert team["members"]
    member = team["members"][0]
    assert {"commitsPerWeek", "avgReviewTimeDays", "onGoalRate", "activityStatus"} <= set(
        member
    )
    assert 0 <= member["onGoalRate"] <= 100


def test_team_health_reflects_open_anomalies(client):
    team = client.get(f"/teams/{TEAM_ID}").json()

    # The seeded team went quiet and is sitting on a three-week-old PR.
    assert team["healthScore"] < 100
    assert team["status"] in {"at-risk", "critical"}
    assert team["busFactorAreas"]
    assert team["busFactorAreas"][0]["riskLevel"] in {"low", "medium", "high"}
    # Sparkline data for the overview card: a fortnight of daily commit counts.
    assert len(team["activity"]) > 1
    assert team["activity"][-1] == 0.0  # the team has gone quiet


def test_unknown_team_is_a_404(client):
    assert client.get("/teams/does-not-exist").status_code == 404


def test_team_metrics_and_history(client):
    payload = client.get(f"/teams/{TEAM_ID}/metrics").json()

    metric_ids = {metric["id"] for metric in payload["metrics"]}
    assert {"commit-activity", "pr-review-time"} <= metric_ids
    for metric in payload["metrics"]:
        assert metric["direction"] in {"up", "down", "flat"}
        assert metric["trend"] in {"good", "caution", "bad"}

    history = payload["reviewTimeHistory"]
    assert history
    assert {"date", "reviewTimeDays", "baselineDays"} == set(history[0])


def test_commit_drop_shows_up_as_a_bad_metric(client):
    metrics = client.get(f"/teams/{TEAM_ID}/metrics").json()["metrics"]
    commits = next(m for m in metrics if m["id"] == "commit-activity")

    # The KPI card smooths over a trailing week, so three silent days read as a
    # sizeable dip rather than the total collapse the daily engine flags.
    assert commits["direction"] == "down"
    assert commits["trend"] in {"caution", "bad"}
    assert commits["delta"] <= -15
    assert commits["value"] < commits["baseline"]


def test_team_anomalies_are_severity_sorted(client):
    anomalies = client.get(f"/teams/{TEAM_ID}/anomalies").json()

    assert anomalies
    rank = {"critical": 0, "warning": 1, "info": 2}
    severities = [rank[a["severity"]] for a in anomalies]
    assert severities == sorted(severities)
    assert anomalies[0]["teamId"] == TEAM_ID
    # Explicit UTC: the browser must not read a naive stamp as local time.
    assert anomalies[0]["detectedAt"].endswith("Z")


def test_anomalies_feed_filters_by_severity(client):
    everything = client.get("/anomalies").json()
    critical = client.get("/anomalies", params={"severity": "critical"}).json()

    assert everything
    assert all(a["severity"] == "critical" for a in critical)
    assert len(critical) <= len(everything)


def test_bus_factor_endpoint(client):
    areas = client.get(f"/teams/{TEAM_ID}/bus-factor").json()

    assert areas
    assert areas[0]["ownershipPercent"] > 0
    assert areas[0]["topOwner"]


def test_summary_is_404_until_the_resolver_has_run(client):
    assert client.get(f"/teams/{TEAM_ID}/summary").status_code == 404


def test_summary_serves_the_cached_verdict(client, seeded):
    upsert_summary(
        seeded,
        SummaryRow(
            team=TEAM,
            summary="Team went quiet after the reviewer bottleneck.",
            root_cause="Reviewer bottleneck",
            remediation_steps=json.dumps(["Rebalance PR review load", "Pair on BGP"]),
            verify_signal="Commits back above 4/day",
            on_goal_score=64.0,
            generated_at=NOW,
        ),
    )

    payload = client.get(f"/teams/{TEAM_ID}/summary").json()

    assert payload["model"] == "Phi-4"
    assert payload["teamId"] == TEAM_ID
    assert payload["suggestions"] == ["Rebalance PR review load", "Pair on BGP"]


def test_ask_streams_tokens(client, monkeypatch):
    def fake_stream(team, question, anomalies, **_):
        assert question == "Why did commits drop?"
        yield from ("Because ", "reviews ", "stalled.")

    monkeypatch.setattr("app.api.routes.teams.stream_answer", fake_stream)

    with client.stream(
        "POST", f"/teams/{TEAM_ID}/ask", json={"question": "Why did commits drop?"}
    ) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())

    assert body == "Because reviews stalled."


def test_ask_reports_a_dead_model_instead_of_a_500(client, monkeypatch):
    def dead_stream(*_, **__):
        raise ConnectionError("Foundry Local is not running")
        yield  # pragma: no cover

    monkeypatch.setattr("app.api.routes.teams.stream_answer", dead_stream)

    response = client.post(f"/teams/{TEAM_ID}/ask", json={"question": "hi"})

    assert response.status_code == 200
    assert "could not reach the local model" in response.text


def test_ask_rejects_an_empty_question(client):
    assert client.post(f"/teams/{TEAM_ID}/ask", json={"question": ""}).status_code == 422


def test_admin_refresh_runs_without_network_or_model(client):
    payload = client.post(
        "/admin/refresh",
        params={"collect": False, "resolve": False, "notify": False},
    ).json()

    assert payload["collected"] is False
    assert payload["teams"] == 1
    assert payload["metricRows"] > 0


def test_resolutions_log_is_exposed(client):
    assert client.get("/admin/resolutions").json() == []


def test_app_logs_are_visible_under_uvicorn(monkeypatch):
    """Without this wiring every logger.info in the app goes nowhere."""
    import logging

    from app.main import configure_logging

    app_logger = logging.getLogger("app")
    original_handlers = app_logger.handlers[:]
    original_propagate = app_logger.propagate
    app_logger.handlers = []

    uvicorn_handler = logging.NullHandler()
    monkeypatch.setattr(
        logging.getLogger("uvicorn"), "handlers", [uvicorn_handler], raising=False
    )
    try:
        configure_logging()
        assert uvicorn_handler in app_logger.handlers
        assert app_logger.level == logging.INFO
    finally:
        app_logger.handlers = original_handlers
        app_logger.propagate = original_propagate


def test_each_request_gets_its_own_database_handle():
    """A shared DuckDB connection across threads returns empty results, not errors."""
    from app.api.deps import get_db

    first = get_db()
    second = get_db()

    assert first is not second
    # Both still see the same database.
    assert first.execute("SELECT 1").fetchone() == second.execute("SELECT 1").fetchone()


def test_settings_never_leak_the_token(client):
    """The page needs to know whether a token exists, and nothing more."""
    payload = client.get("/admin/settings").json()

    assert payload["dataSource"] in {"demo", "github"}
    assert isinstance(payload["githubTokenConfigured"], bool)
    assert "githubToken" not in payload
    assert "token" not in json.dumps(payload).lower().replace("tokenconfigured", "")


def test_settings_update_round_trips(client):
    updated = client.put(
        "/admin/settings",
        json={"dataSource": "demo", "githubRepos": ["microsoft/vscode", " "]},
    ).json()

    assert updated["dataSource"] == "demo"
    assert updated["githubRepos"] == ["microsoft/vscode"]
    assert client.get("/admin/settings").json()["dataSource"] == "demo"


def test_seed_demo_fills_the_dashboard(client):
    payload = client.post("/admin/seed-demo").json()

    assert payload["teams"] == 3
    assert payload["commits"] > 0
    assert payload["resolutions"] > 0
    assert payload["summaries"] == 3
    assert payload["anomaliesOpen"] > 0

    teams = client.get("/teams").json()
    assert len(teams) == 3
    assert client.get("/admin/resolutions").json()
    # Every seeded team has a cached verdict, so no summary card 404s.
    for team in teams:
        assert client.get(f"/teams/{team['id']}/summary").status_code == 200


def test_demo_data_is_never_topped_up_with_a_live_sync(client, monkeypatch):
    """Mixing fabricated and collected rows would make both untrue."""
    client.put("/admin/settings", json={"dataSource": "demo"})

    called = False

    async def fail_if_called():
        nonlocal called
        called = True

    monkeypatch.setattr("app.collectors.github.collect_all", fail_if_called)

    payload = client.post(
        "/admin/refresh", params={"resolve": False, "notify": False}
    ).json()

    assert called is False
    assert payload["collected"] is False
