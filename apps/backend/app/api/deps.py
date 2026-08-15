"""Shared FastAPI dependencies.

The database handle goes through a dependency rather than being imported
directly by the routes, so tests can point the whole API at a seeded in-memory
DuckDB with `app.dependency_overrides[get_db] = ...`.
"""

from __future__ import annotations

from typing import Annotated

import duckdb
from fastapi import Depends, HTTPException, status

from app.api.services import resolve_team_name
from app.core.db import get_connection


def get_db() -> duckdb.DuckDBPyConnection:
    """A per-request cursor onto the shared database.

    DuckDB's Python connection is not thread-safe. FastAPI runs sync route
    handlers in a threadpool and the scheduler runs refresh passes in worker
    threads, so a single shared connection gets used from several threads at
    once. That does not raise: it silently returns empty results, which on the
    dashboard looked like a team card reading "Engineers 0" while the same
    response still carried that team's bus-factor owner. `cursor()` hands each
    caller its own handle onto the same database file.
    """
    return get_connection().cursor()


DbConn = Annotated[duckdb.DuckDBPyConnection, Depends(get_db)]


def get_team_name(team_id: str, conn: DbConn) -> str:
    """Resolve a URL slug to a stored team name, or 404."""
    team = resolve_team_name(conn, team_id)
    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown team: {team_id}"
        )
    return team


TeamName = Annotated[str, Depends(get_team_name)]
