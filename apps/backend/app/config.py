"""Typed application settings, loaded from .env via pydantic-settings."""

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def _split_csv(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        return value
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Local LLM (OpenAI-compatible endpoint: Foundry Local or Ollama)
    LLM_BASE_URL: str
    LLM_API_KEY: str
    LLM_MODEL: str

    # Embeddings
    EMBEDDING_MODEL: str

    # GitHub
    GITHUB_TOKEN: str = ""
    GITHUB_REPOS: Annotated[list[str], NoDecode] = []

    # Storage
    DUCKDB_PATH: Path
    CHROMA_PATH: Path

    # Microsoft Teams webhook (proactive alerts)
    TEAMS_WEBHOOK_URL: str = ""

    # Background refresh (collect -> rollup -> anomalies -> resolver)
    SCHEDULER_ENABLED: bool = True
    REFRESH_INTERVAL_MINUTES: int = 30
    # Weekly digest, in the scheduler's timezone (UTC).
    DIGEST_DAY_OF_WEEK: str = "mon"
    DIGEST_HOUR: int = 8

    # Optional sprint goal used by the resolver's on-goal reasoning.
    SPRINT_GOAL: str = ""

    # API server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: Annotated[list[str], NoDecode] = []

    @field_validator("GITHUB_REPOS", "CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_csv(cls, value: str | list[str]) -> list[str]:
        return _split_csv(value)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
