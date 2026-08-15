"""All API routers, combined under one prefix-free parent."""

from fastapi import APIRouter

from app.api.routes import admin, anomalies, digest, teams

api_router = APIRouter()
api_router.include_router(teams.router)
api_router.include_router(anomalies.router)
api_router.include_router(digest.router)
api_router.include_router(admin.router)

__all__ = ["api_router"]
