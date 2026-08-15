"""Text embeddings via sentence-transformers (bge-m3 by default).

bge-m3 is multilingual and gives solid retrieval quality for short commit and
PR text. The model is heavy (~2GB) and slow to load, so it is created lazily
and cached process-wide; nothing here touches the model until the first
`embed()` call. Callers pass plain strings and get back plain float lists so
the rest of the app never imports torch/numpy types.
"""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache
from typing import TYPE_CHECKING

from app.config import get_settings

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


@lru_cache
def _get_model() -> SentenceTransformer:
    # Imported inside the function so importing this module stays cheap and
    # test code can monkeypatch `embed` without pulling in sentence-transformers.
    from sentence_transformers import SentenceTransformer

    settings = get_settings()
    return SentenceTransformer(settings.EMBEDDING_MODEL)


def embed(texts: Sequence[str]) -> list[list[float]]:
    """Embed a batch of texts into normalized vectors."""
    if not texts:
        return []
    model = _get_model()
    vectors = model.encode(
        list(texts),
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return [vector.tolist() for vector in vectors]


def embed_one(text: str) -> list[float]:
    """Convenience for a single query string."""
    return embed([text])[0]
