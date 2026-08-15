"""Persistent ChromaDB store of team activity text for retrieval.

Commit messages (and PR descriptions, once the collector stores their bodies)
are embedded with bge-m3 and kept in a single cosine-space collection tagged by
team, so the resolver can pull the handful of most relevant snippets when it
explains an anomaly. Embeddings are computed here via `ai.embeddings.embed`
rather than letting Chroma download its own model, keeping one embedding model
across the app.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache
from typing import TYPE_CHECKING

import duckdb

from app.ai.embeddings import embed, embed_one
from app.config import get_settings
from app.core.clock import utcnow
from app.core.db import get_commit_docs_for_team

if TYPE_CHECKING:
    from chromadb.api import ClientAPI
    from chromadb.api.models.Collection import Collection

COLLECTION_NAME = "activity"
DEFAULT_INDEX_LOOKBACK_DAYS = 90
DEFAULT_RETRIEVE_K = 5


@dataclass(frozen=True, slots=True)
class RetrievedDoc:
    text: str
    repo: str
    author: str
    kind: str
    distance: float


@dataclass(slots=True)
class VectorStore:
    """Thin wrapper over one Chroma collection of embedded activity text."""

    collection: Collection

    def index_documents(
        self,
        ids: Sequence[str],
        texts: Sequence[str],
        metadatas: Sequence[dict[str, str]],
    ) -> int:
        """Upsert a batch of pre-associated (id, text, metadata) triples."""
        if not ids:
            return 0
        self.collection.upsert(
            ids=list(ids),
            documents=list(texts),
            embeddings=embed(texts),  # type: ignore[arg-type]
            metadatas=list(metadatas),  # type: ignore[arg-type]
        )
        return len(ids)

    def index_team_commits(
        self,
        conn: duckdb.DuckDBPyConnection,
        team: str,
        lookback_days: int = DEFAULT_INDEX_LOOKBACK_DAYS,
        now: datetime | None = None,
    ) -> int:
        """Embed and store a team's recent commit messages."""
        now = now or utcnow()
        since = now - timedelta(days=lookback_days)
        docs = get_commit_docs_for_team(conn, team, since)
        docs = [d for d in docs if d.message.strip()]
        if not docs:
            return 0
        ids = [f"commit:{d.sha}" for d in docs]
        texts = [d.message for d in docs]
        metadatas = [
            {"team": team, "repo": d.repo, "author": d.author, "kind": "commit"}
            for d in docs
        ]
        return self.index_documents(ids, texts, metadatas)

    def retrieve_context(
        self, team: str, query: str, n_results: int = DEFAULT_RETRIEVE_K
    ) -> list[RetrievedDoc]:
        """Most relevant activity snippets for a team, nearest first."""
        result = self.collection.query(
            query_embeddings=[embed_one(query)],  # type: ignore[list-item]
            n_results=n_results,
            where={"team": team},
            include=["documents", "metadatas", "distances"],
        )
        docs = (result.get("documents") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]
        dists = (result.get("distances") or [[]])[0]
        retrieved: list[RetrievedDoc] = []
        for text, meta, dist in zip(docs, metas, dists, strict=False):
            meta = meta or {}
            retrieved.append(
                RetrievedDoc(
                    text=text or "",
                    repo=str(meta.get("repo", "")),
                    author=str(meta.get("author", "")),
                    kind=str(meta.get("kind", "")),
                    distance=float(dist),
                )
            )
        return retrieved


@lru_cache
def _get_client() -> ClientAPI:
    import chromadb

    settings = get_settings()
    settings.CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(settings.CHROMA_PATH))


@lru_cache
def get_vectorstore() -> VectorStore:
    """Process-wide vector store backed by a persistent Chroma collection."""
    collection = _get_client().get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    return VectorStore(collection=collection)
