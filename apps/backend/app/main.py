"""FastAPI application factory and startup."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.config import get_settings
from app.core.db import get_connection
from app.core.schemas import HealthResponse
from app.scheduler import build_scheduler, startup_pass

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Open the database, warm derived state, run the background jobs."""
    settings = get_settings()
    get_connection()

    scheduler = None
    if settings.SCHEDULER_ENABLED:
        scheduler = build_scheduler(settings)
        scheduler.start()
        logger.info(
            "Scheduler started: refresh every %d min, digest %s at %02d:00 UTC",
            settings.REFRESH_INTERVAL_MINUTES,
            settings.DIGEST_DAY_OF_WEEK,
            settings.DIGEST_HOUR,
        )

    # Fire and forget: the API is up immediately, the first pass lands shortly.
    warmup = asyncio.create_task(startup_pass())

    try:
        yield
    finally:
        warmup.cancel()
        if scheduler is not None:
            scheduler.shutdown(wait=False)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Watchtower API",
        version="0.1.0",
        summary="Engineering-health signals, anomalies, and Phi-4 guidance.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=HealthResponse, tags=["meta"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    app.include_router(api_router)
    return app


app = create_app()
