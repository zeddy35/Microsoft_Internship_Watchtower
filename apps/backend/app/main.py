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


def configure_logging(level: int = logging.INFO) -> None:
    """Make Watchtower's own logs visible under uvicorn.

    Uvicorn configures handlers for its own loggers and leaves the root logger
    bare, so without this every logger.info in the app - the scheduler
    starting, an anomaly pass, a failed Teams post - goes nowhere. Borrowing
    uvicorn's handler keeps the format consistent instead of printing two
    different log styles side by side.
    """
    app_logger = logging.getLogger("app")
    if app_logger.handlers:
        return

    uvicorn_logger = logging.getLogger("uvicorn")
    if uvicorn_logger.handlers:
        for handler in uvicorn_logger.handlers:
            app_logger.addHandler(handler)
        app_logger.propagate = False
    elif not logging.getLogger().handlers:
        # Running outside uvicorn (a script, a test) - basic output is fine.
        logging.basicConfig(level=level)

    app_logger.setLevel(level)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Open the database, warm derived state, run the background jobs."""
    settings = get_settings()
    configure_logging()
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
