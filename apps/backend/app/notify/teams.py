"""Microsoft Teams notifications: critical alerts and the weekly digest.

Watchtower is only useful if it reaches a lead where they already are, so the
high-severity path pushes an adaptive card into a Teams channel instead of
waiting for someone to open the dashboard. Each anomaly is alerted on exactly
once - `anomaly_events.notified_at` is the idempotency guard, so a refresh
every 30 minutes does not turn into a notification every 30 minutes.

With TEAMS_WEBHOOK_URL unset the whole module degrades to a logged warning,
which is the normal state on a laptop demo.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import duckdb
import httpx

from app.config import get_settings
from app.core.clock import utcnow
from app.core.db import (
    AnomalyEventRow,
    get_summary,
    get_unnotified_events,
    list_teams,
    mark_events_notified,
)

logger = logging.getLogger(__name__)

ALERT_SEVERITIES = ("critical",)
REQUEST_TIMEOUT_SECONDS = 15.0

SEVERITY_COLOR = {"critical": "attention", "warning": "warning", "info": "accent"}


def _text_block(text: str, **kwargs: Any) -> dict[str, Any]:
    return {"type": "TextBlock", "text": text, "wrap": True, **kwargs}


def _card(body: list[dict[str, Any]]) -> dict[str, Any]:
    """Wrap card body elements in the message envelope a webhook expects."""
    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": body,
                },
            }
        ],
    }


def build_anomaly_card(
    event: AnomalyEventRow, *, explanation: str = "", action: str = ""
) -> dict[str, Any]:
    """One adaptive card for one flagged anomaly."""
    body: list[dict[str, Any]] = [
        _text_block(
            f"Watchtower · {event.severity.upper()}",
            weight="Bolder",
            size="Small",
            color=SEVERITY_COLOR.get(event.severity, "default"),
        ),
        _text_block(event.title, weight="Bolder", size="Medium"),
        _text_block(
            f"Team: **{event.team}**  ·  detected {event.detected_at:%Y-%m-%d %H:%M} UTC",
            isSubtle=True,
            size="Small",
        ),
        _text_block(event.description),
    ]
    if explanation:
        body.append(_text_block(f"**Phi-4:** {explanation}"))
    if action:
        body.append(_text_block(f"**Recommended:** {action}"))
    return _card(body)


def build_digest_card(team: str, summary: str, suggestions: list[str]) -> dict[str, Any]:
    body: list[dict[str, Any]] = [
        _text_block("Watchtower · weekly digest", weight="Bolder", size="Small"),
        _text_block(team, weight="Bolder", size="Medium"),
        _text_block(summary),
    ]
    if suggestions:
        bullets = "\n".join(f"- {item}" for item in suggestions)
        body.append(_text_block(f"**Recommended next steps**\n{bullets}"))
    return _card(body)


async def post_card(card: dict[str, Any]) -> bool:
    """POST one card to the configured webhook. False when unset or failing."""
    settings = get_settings()
    if not settings.TEAMS_WEBHOOK_URL:
        logger.warning("TEAMS_WEBHOOK_URL is not set; skipping Teams notification")
        return False

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(settings.TEAMS_WEBHOOK_URL, json=card)
            response.raise_for_status()
    except httpx.HTTPError:
        logger.exception("Failed to post a card to Teams")
        return False
    return True


def _summary_parts(
    conn: duckdb.DuckDBPyConnection, team: str
) -> tuple[str, list[str]]:
    """Cached Phi-4 text for a team: (summary, remediation steps)."""
    row = get_summary(conn, team)
    if row is None:
        return "", []
    try:
        steps = [str(step) for step in json.loads(row.remediation_steps)]
    except (TypeError, ValueError):
        steps = []
    return row.summary, steps


async def notify_critical_anomalies(conn: duckdb.DuckDBPyConnection) -> int:
    """Alert once per newly opened high-severity anomaly. Returns cards sent."""
    events = get_unnotified_events(conn, ALERT_SEVERITIES)
    if not events:
        return 0

    sent: list[str] = []
    for event in events:
        explanation, steps = _summary_parts(conn, event.team)
        delivered = await post_card(
            build_anomaly_card(
                event,
                explanation=explanation,
                action=steps[0] if steps else "",
            )
        )
        if not delivered:
            # Leave notified_at unset so the next cycle retries this alert.
            break
        sent.append(event.id)

    mark_events_notified(conn, sent, utcnow())
    return len(sent)


async def send_weekly_digest(conn: duckdb.DuckDBPyConnection) -> int:
    """One digest card per team, from the cached resolver output."""
    sent = 0
    for team in list_teams(conn):
        summary, steps = _summary_parts(conn, team)
        if not summary:
            continue
        if await post_card(build_digest_card(team, summary, steps)):
            sent += 1
    logger.info("Weekly digest: %d team cards sent", sent)
    return sent
