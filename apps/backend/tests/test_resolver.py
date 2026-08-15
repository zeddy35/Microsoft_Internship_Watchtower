"""Resolver: prompt shape and defensive parsing of a local model's output.

Local models are not reliable JSON emitters, so the parser is tested against
the ways they actually misbehave: prose around the object, a string where a
list belongs, a score outside the range.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

import pytest

from app.ai.resolver import (
    Resolution,
    build_prompt,
    build_question_prompt,
    parse_resolution,
    resolve_team,
    stream_answer,
)
from app.ai.vectorstore import RetrievedDoc
from app.anomaly.engine import Anomaly, Severity
from tests.conftest import NOW, TEAM

ANOMALY = Anomaly(
    team=TEAM,
    metric="commits_per_day",
    severity=Severity.CRITICAL,
    title="Commit volume dropped",
    description="Commits fell to 0/day against a baseline of 6/day.",
    detected_at=NOW,
    observed=0.0,
    baseline=6.0,
    z_score=-4.1,
)

DOC = RetrievedDoc(
    text="Fix BGP peering timeout #421",
    repo="microsoft/vscode",
    author="elena",
    kind="commit",
    distance=0.1,
)


@dataclass
class FakeClient:
    """Stands in for Phi4Client without importing openai's network path."""

    response: str = "{}"
    chunks: tuple[str, ...] = ()
    last_prompt: str = ""

    def ask(self, prompt: str, **_: object) -> str:
        self.last_prompt = prompt
        return self.response

    def stream(self, prompt: str, **_: object) -> Iterator[str]:
        self.last_prompt = prompt
        yield from self.chunks


@dataclass
class FakeStore:
    docs: tuple[RetrievedDoc, ...] = (DOC,)

    def retrieve_context(self, team: str, query: str, n_results: int = 5):
        return list(self.docs)


def test_prompt_includes_anomalies_context_and_goal():
    prompt = build_prompt(TEAM, [ANOMALY], [DOC], "Ship the peering rewrite")

    assert TEAM in prompt
    assert "Ship the peering rewrite" in prompt
    assert "Commit volume dropped" in prompt
    assert "Fix BGP peering timeout #421" in prompt
    assert "on_goal_score" in prompt  # the JSON shape it must return


def test_parse_resolution_tolerates_prose_around_the_json():
    raw = (
        "Sure! Here is my analysis:\n"
        '{"summary": "Team went quiet.", "root_cause": "Reviewer bottleneck", '
        '"remediation_steps": ["Rebalance reviews", "Pair on BGP"], '
        '"verify_signal": "Review time back under 1 day", "on_goal_score": 64}\n'
        "Hope that helps!"
    )

    resolution = parse_resolution(TEAM, raw)

    assert resolution.summary == "Team went quiet."
    assert resolution.remediation_steps == ["Rebalance reviews", "Pair on BGP"]
    assert resolution.on_goal_score == 64.0


def test_parse_resolution_coerces_sloppy_fields():
    raw = (
        '{"summary": "x", "root_cause": "y", "remediation_steps": "Just one step", '
        '"verify_signal": "z", "on_goal_score": "150"}'
    )

    resolution = parse_resolution(TEAM, raw)

    assert resolution.remediation_steps == ["Just one step"]
    assert resolution.on_goal_score == 100.0  # clamped into range


def test_parse_resolution_rejects_a_response_with_no_json():
    with pytest.raises(ValueError):
        parse_resolution(TEAM, "I cannot help with that.")


def test_resolve_team_returns_a_typed_resolution(conn):
    client = FakeClient(
        response='{"summary": "s", "root_cause": "r", '
        '"remediation_steps": ["a"], "verify_signal": "v", "on_goal_score": 70}'
    )

    resolution = resolve_team(
        conn, TEAM, [ANOMALY], client=client, store=FakeStore()
    )

    assert isinstance(resolution, Resolution)
    assert resolution.on_goal_score == 70.0
    assert "Commit volume dropped" in client.last_prompt


def test_stream_answer_yields_model_chunks():
    client = FakeClient(chunks=("Review ", "time ", "is the issue."))

    chunks = list(
        stream_answer(
            TEAM, "What is wrong?", [ANOMALY], client=client, store=FakeStore()
        )
    )

    assert "".join(chunks) == "Review time is the issue."
    assert "What is wrong?" in client.last_prompt


def test_question_prompt_grounds_the_model_in_evidence():
    prompt = build_question_prompt(TEAM, "Why are we slow?", [ANOMALY], [DOC])

    assert "Why are we slow?" in prompt
    assert "Commit volume dropped" in prompt
    assert "elena" in prompt
