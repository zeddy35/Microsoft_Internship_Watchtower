"""The weekly digest, as a page and as a Teams post.

Same content either way: the scheduler posts it to a channel every Monday, and
this route renders it for anyone who would rather look than wait for the card.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api import services
from app.api.deps import DbConn
from app.config import get_settings
from app.core.schemas import DigestOut, SendDigestResult
from app.notify.teams import send_weekly_digest

router = APIRouter(tags=["digest"])


@router.get("/digest", response_model=DigestOut)
def get_digest_route(
    conn: DbConn,
    days: int = Query(
        default=services.DIGEST_PERIOD_DAYS,
        ge=1,
        le=90,
        description="Length of the digest period, in days",
    ),
) -> DigestOut:
    return services.build_digest(conn, days=days)


@router.post("/admin/send-digest", response_model=SendDigestResult)
async def send_digest_route(conn: DbConn) -> SendDigestResult:
    """Post the digest to Teams now, instead of waiting for Monday.

    With no webhook configured this is a no-op that says so, rather than an
    error: not having a channel wired up is a normal state on a laptop.
    """
    configured = bool(get_settings().TEAMS_WEBHOOK_URL)
    sent = await send_weekly_digest(conn) if configured else 0
    return SendDigestResult(sent=sent, webhook_configured=configured)
