"""Teams notifier: card shape, the once-only guard, and the unset-webhook path."""

from __future__ import annotations

import pytest

from app.core.db import get_unnotified_events, upsert_anomaly_event
from app.notify import teams as notify
from tests.conftest import NOW, TEAM


def _open_critical(conn, metric="commits_per_day"):
    return upsert_anomaly_event(
        conn,
        team=TEAM,
        metric=metric,
        severity="critical",
        title="Commit volume dropped",
        description="Commits fell to 0/day against a baseline of 6/day.",
        observed=0.0,
        baseline=6.0,
        z_score=-4.1,
        seen_at=NOW,
    )


def test_card_carries_the_anomaly_and_the_recommendation(conn):
    _open_critical(conn)
    event = get_unnotified_events(conn, ("critical",))[0]

    card = notify.build_anomaly_card(
        event, explanation="Reviewer bottleneck", action="Rebalance review load"
    )

    content = card["attachments"][0]["content"]
    assert content["type"] == "AdaptiveCard"
    text = " ".join(block["text"] for block in content["body"])
    assert "Commit volume dropped" in text
    assert TEAM in text
    assert "Reviewer bottleneck" in text
    assert "Rebalance review load" in text


@pytest.mark.asyncio
async def test_no_webhook_means_no_alert_and_no_state_change(conn, monkeypatch):
    """On a laptop demo the webhook is unset; that must not consume the alert."""
    _open_critical(conn)
    monkeypatch.setattr(notify, "post_card", _always_fails)

    sent = await notify.notify_critical_anomalies(conn)

    assert sent == 0
    # Still unnotified, so it will be alerted once a webhook is configured.
    assert len(get_unnotified_events(conn, ("critical",))) == 1


@pytest.mark.asyncio
async def test_each_anomaly_is_alerted_exactly_once(conn, monkeypatch):
    _open_critical(conn)
    _open_critical(conn, metric="review_time_hours")
    posted: list[dict] = []

    async def capture(card):
        posted.append(card)
        return True

    monkeypatch.setattr(notify, "post_card", capture)

    assert await notify.notify_critical_anomalies(conn) == 2
    assert await notify.notify_critical_anomalies(conn) == 0
    assert len(posted) == 2


@pytest.mark.asyncio
async def test_weekly_digest_skips_teams_without_a_summary(seeded, monkeypatch):
    posted: list[dict] = []

    async def capture(card):
        posted.append(card)
        return True

    monkeypatch.setattr(notify, "post_card", capture)

    assert await notify.send_weekly_digest(seeded) == 0
    assert posted == []


async def _always_fails(card):
    return False
