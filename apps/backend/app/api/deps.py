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
    return get_connection()


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
