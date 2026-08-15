"""The detect -> verify loop, which is what turns anomalies into labeled data."""

from __future__ import annotations

import json
from datetime import timedelta

from app.core.db import (
    CommitRow,
    SummaryRow,
    get_open_anomaly_events,
    get_summary,
    insert_commits,
    list_resolutions,
    upsert_summary,
)
from app.jobs import run_anomaly_pass, run_resolver_pass
from app.metrics.rollup import rollup_metrics
from tests.conftest import NOW, QUIET_DAYS, REPO, TEAM
from tests.test_resolver import FakeClient, FakeStore


def _recover(conn, now):
    """Backfill the quiet days with normal activity, as if the team came back."""
    rows = []
    for day_offset in range(QUIET_DAYS + 1):
        day = now - timedelta(days=day_offset)
        for index in range(7):
            rows.append(
                CommitRow(
                    sha=f"recovery-{day_offset}-{index}",
                    repo=REPO,
                    author="elena",
                    message=f"Fix regression #{index}",
                    additions=5,
                    deletions=1,
                    committed_at=day.replace(hour=10, minute=0, second=0),
                )
            )
    insert_commits(conn, rows)


def test_anomaly_pass_opens_events(seeded):
    rollup_metrics(seeded, until=(NOW + timedelta(days=1)).date())

    result = run_anomaly_pass(seeded, now=NOW)

    assert result.open_count > 0
    assert result.opened == result.open_count
    assert result.cleared == 0
    assert len(get_open_anomaly_events(seeded, TEAM)) == result.open_count


def test_verify_pass_closes_recovered_anomalies_and_labels_them(seeded):
    """The loop's payoff: a cleared anomaly becomes a row of training data."""
    rollup_metrics(seeded, until=(NOW + timedelta(days=1)).date())
    upsert_summary(
        seeded,
        SummaryRow(
            team=TEAM,
            summary="Team went quiet",
            root_cause="Reviewer bottleneck",
            remediation_steps=json.dumps(["Rebalance PR review load"]),
            verify_signal="Commits back above 4/day",
            on_goal_score=64.0,
            generated_at=NOW,
        ),
    )
    first = run_anomaly_pass(seeded, now=NOW)
    assert first.open_count > 0

    _recover(seeded, NOW)
    later = NOW + timedelta(hours=6)
    rollup_metrics(seeded, until=(later + timedelta(days=1)).date())
    second = run_anomaly_pass(seeded, now=later)

    assert second.cleared > 0
    resolutions = list_resolutions(seeded, TEAM)
    assert resolutions
    assert resolutions[0].outcome == "cleared"
    # The recommendation that was live at the time is stored with the label.
    assert resolutions[0].action == "Rebalance PR review load"
    assert resolutions[0].open_days > 0


def test_anomaly_pass_is_stable_when_nothing_changes(seeded):
    rollup_metrics(seeded, until=(NOW + timedelta(days=1)).date())
    first = run_anomaly_pass(seeded, now=NOW)
    second = run_anomaly_pass(seeded, now=NOW + timedelta(minutes=30))

    assert second.open_count == first.open_count
    assert second.opened == 0
    assert second.cleared == 0
    assert list_resolutions(seeded, TEAM) == []


def test_resolver_pass_caches_a_summary(seeded):
    rollup_metrics(seeded, until=(NOW + timedelta(days=1)).date())
    client = FakeClient(
        response='{"summary": "Quiet week", "root_cause": "Reviews", '
        '"remediation_steps": ["Rebalance"], "verify_signal": "v", '
        '"on_goal_score": 64}'
    )

    written = run_resolver_pass(seeded, client=client, store=FakeStore(), now=NOW)

    assert written == 1
    stored = get_summary(seeded, TEAM)
    assert stored is not None
    assert stored.summary == "Quiet week"
    assert json.loads(stored.remediation_steps) == ["Rebalance"]


def test_resolver_pass_survives_a_dead_model(seeded):
    """A local endpoint that is not running must not take the refresh down."""

    class DeadClient:
        def ask(self, *_: object, **__: object) -> str:
            raise ConnectionError("Foundry Local is not running")

    written = run_resolver_pass(
        seeded, client=DeadClient(), store=FakeStore(), now=NOW
    )

    assert written == 0
    assert get_summary(seeded, TEAM) is None
