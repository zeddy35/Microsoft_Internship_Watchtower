"""Phi-4 client over any OpenAI-compatible endpoint (Foundry Local or Ollama).

Watchtower talks to a *local* model, so the base URL and key come from settings
rather than the OpenAI default. The client is deliberately thin: a blocking
`ask()` for one-shot generations (summaries, resolver JSON) and a `stream()`
generator for the chat endpoint. Temperature defaults low — this is analysis,
not creative writing.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from functools import lru_cache

from openai import OpenAI

from app.config import get_settings

DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 1024


@dataclass(slots=True)
class Phi4Client:
    """Minimal wrapper around an OpenAI-compatible chat completions endpoint."""

    client: OpenAI
    model: str

    def _messages(
        self, prompt: str, system: str | None
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return messages

    def ask(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> str:
        """One-shot completion, returned as a single string."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self._messages(prompt, system),  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        return response.choices[0].message.content or ""

    def stream(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> Iterator[str]:
        """Yield content deltas as they arrive, for token-by-token UI streaming."""
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=self._messages(prompt, system),  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


@lru_cache
def get_phi4_client() -> Phi4Client:
    """Process-wide Phi-4 client built from LLM_* settings."""
    settings = get_settings()
    client = OpenAI(base_url=settings.LLM_BASE_URL, api_key=settings.LLM_API_KEY)
    return Phi4Client(client=client, model=settings.LLM_MODEL)
