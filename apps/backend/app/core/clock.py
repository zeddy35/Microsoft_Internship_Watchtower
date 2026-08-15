"""One source of truth for "now".

DuckDB's TIMESTAMP column is timezone-naive and the GitHub collector stores
naive-UTC values, so every comparison in the app has to use naive UTC too.
Mixing an aware `datetime.now(UTC)` into a query against those columns is the
kind of bug that only shows up when a baseline silently returns nothing, so
all app code calls `utcnow()` instead.
"""

from __future__ import annotations

from datetime import UTC, date, datetime


def utcnow() -> datetime:
    """Current UTC time as a naive datetime, matching what DuckDB stores."""
    return datetime.now(UTC).replace(tzinfo=None)


def utctoday() -> date:
    """Current UTC date."""
    return utcnow().date()


def as_naive_utc(value: datetime) -> datetime:
    """Drop the tzinfo from an aware datetime after converting it to UTC."""
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)
