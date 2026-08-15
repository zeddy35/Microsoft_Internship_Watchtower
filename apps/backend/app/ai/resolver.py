"""Resolver loop: turn a team's anomalies + retrieved activity into guidance.

This is the reasoning core. Given the anomalies the engine flagged and the most
relevant commit/PR snippets from the vector store, it prompts Phi-4 for a
structured verdict: a plain-English summary, the likely root cause, a ranked
list of remediation steps, one concrete signal to watch to confirm recovery,
and an on-goal score (how much recent work matches the sprint goal). The model
is asked for strict JSON so the result maps cleanly onto typed fields; parsing
is defensive because local models occasionally wrap JSON in prose.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass, field

import duckdb

from app.ai.phi4_client import Phi4Client, get_phi4_client
from app.ai.vectorstore import RetrievedDoc, VectorStore, get_vectorstore
from app.anomaly.engine import Anomaly

MAX_CONTEXT_SNIPPETS = 6
RESOLVER_TEMPERATURE = 0.1

SYSTEM_PROMPT = (
    "You are Watchtower, an engineering-health analyst for Microsoft teams. "
    "You explain delivery anomalies plainly and recommend concrete, prioritized "
    "actions a lead can take. Be specific and grounded in the evidence provided. "
    "Respond with a single JSON object and nothing else."
)

_JSON_SCHEMA_HINT = (
    "{\n"
    '  "summary": "2-3 sentence plain-English health summary",\n'
    '  "root_cause": "the single most likely underlying cause",\n'
    '  "remediation_steps": ["highest-priority action first", "..."],\n'
    '  "verify_signal": "one measurable signal that would confirm recovery",\n'
    '  "on_goal_score": 0-100  // share of recent work matching the sprint goal\n'
    "}"
)


@dataclass(slots=True)
class Resolution:
    team: str
    summary: str
    root_cause: str
    remediation_steps: list[str] = field(default_factory=list)
    verify_signal: str = ""
    on_goal_score: float = 0.0


# --- prompt construction ----------------------------------------------------


def _format_anomalies(anomalies: list[Anomaly]) -> str:
    if not anomalies:
        return "No anomalies flagged; assess overall health from the context."
    lines = []
    for a in anomalies:
        lines.append(
            f"- [{a.severity}] {a.title}: {a.description} "
            f"(observed {a.observed:.1f}, baseline {a.baseline:.1f})"
        )
    return "\n".join(lines)


def _format_context(docs: list[RetrievedDoc]) -> str:
    if not docs:
        return "No recent activity retrieved."
    lines = []
    for d in docs[:MAX_CONTEXT_SNIPPETS]:
        snippet = d.text.strip().splitlines()[0][:200] if d.text.strip() else ""
        lines.append(f"- ({d.repo} · {d.author}) {snippet}")
    return "\n".join(lines)


def build_prompt(
    team: str,
    anomalies: list[Anomaly],
    context: list[RetrievedDoc],
    sprint_goal: str | None,
) -> str:
    goal_line = (
        f"Sprint goal: {sprint_goal}\n"
        if sprint_goal
        else "Sprint goal: (not provided; estimate on-goal share loosely)\n"
    )
    return (
        f"Team: {team}\n"
        f"{goal_line}\n"
        f"Flagged anomalies:\n{_format_anomalies(anomalies)}\n\n"
        f"Recent activity (most relevant first):\n{_format_context(context)}\n\n"
        f"Return exactly this JSON shape:\n{_JSON_SCHEMA_HINT}"
    )


# --- response parsing -------------------------------------------------------


def _extract_json(raw: str) -> dict:
    """Pull the first JSON object out of a model response, tolerating prose."""
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("no JSON object found in model response")
    return json.loads(raw[start : end + 1])


def _coerce_steps(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _coerce_score(value: object) -> float:
    try:
        score = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(100.0, score))


def parse_resolution(team: str, raw: str) -> Resolution:
    data = _extract_json(raw)
    return Resolution(
        team=team,
        summary=str(data.get("summary", "")).strip(),
        root_cause=str(data.get("root_cause", "")).strip(),
        remediation_steps=_coerce_steps(data.get("remediation_steps")),
        verify_signal=str(data.get("verify_signal", "")).strip(),
        on_goal_score=_coerce_score(data.get("on_goal_score")),
    )


# --- entry point ------------------------------------------------------------


def resolve_team(
    conn: duckdb.DuckDBPyConnection,
    team: str,
    anomalies: list[Anomaly],
    *,
    sprint_goal: str | None = None,
    client: Phi4Client | None = None,
    store: VectorStore | None = None,
) -> Resolution:
    """Retrieve context, prompt Phi-4, and parse a typed Resolution for a team."""
    client = client or get_phi4_client()
    store = store or get_vectorstore()

    query = "; ".join(a.title for a in anomalies) if anomalies else team
    if sprint_goal:
        query = f"{query}. Goal: {sprint_goal}"
    context = store.retrieve_context(team, query)

    prompt = build_prompt(team, anomalies, context, sprint_goal)
    raw = client.ask(
        prompt, system=SYSTEM_PROMPT, temperature=RESOLVER_TEMPERATURE
    )
    return parse_resolution(team, raw)


# --- ad-hoc questions -------------------------------------------------------

ANSWER_SYSTEM_PROMPT = (
    "You are Watchtower, an engineering-health analyst for Microsoft teams. "
    "Answer the lead's question about this team using only the evidence "
    "provided. Be concise and concrete; if the evidence does not support an "
    "answer, say so plainly. Reply in prose, not JSON."
)


def build_question_prompt(
    team: str,
    question: str,
    anomalies: list[Anomaly],
    context: list[RetrievedDoc],
) -> str:
    return (
        f"Team: {team}\n\n"
        f"Currently flagged anomalies:\n{_format_anomalies(anomalies)}\n\n"
        f"Relevant recent activity:\n{_format_context(context)}\n\n"
        f"Question: {question}"
    )


def stream_answer(
    team: str,
    question: str,
    anomalies: list[Anomaly],
    *,
    client: Phi4Client | None = None,
    store: VectorStore | None = None,
) -> Iterator[str]:
    """Token-by-token answer to a lead's question, grounded in team evidence."""
    client = client or get_phi4_client()
    store = store or get_vectorstore()

    context = store.retrieve_context(team, question)
    prompt = build_question_prompt(team, question, anomalies, context)
    return client.stream(
        prompt, system=ANSWER_SYSTEM_PROMPT, temperature=RESOLVER_TEMPERATURE
    )
