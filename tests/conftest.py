"""Shared test fixtures.

These tests run fully offline using a scripted provider, so no API keys or
network access are required.
"""

from __future__ import annotations

import json

import pytest

from socrates.providers.base import Provider


class ScriptedProvider(Provider):
    """A provider that returns canned responses keyed by the pipeline stage.

    The engine prompts are distinctive enough to route on a substring of the
    user prompt. This lets us drive the whole pipeline deterministically.
    """

    name = "scripted"

    def __init__(self, responses: dict[str, str]):
        # Map: stage keyword -> response string
        self.responses = responses
        self.calls: list[str] = []

    def complete(self, system: str, prompt: str, *, max_tokens: int = 4096) -> str:
        self.calls.append(prompt)
        # Order matters: check the more specific markers first.
        if "critique round" in prompt or "Socratic examiner of the answer" in prompt:
            return self.responses.get("critique", _json({"questions": [], "weaknesses": [], "revised_answer": None, "resolved": True}))
        if "adversarial reviewer" in prompt:
            return self.responses.get("adversarial", _json({"findings": [], "disagreements": []}))
        if "Extract every checkable factual claim" in prompt:
            return self.responses.get("claims", "[]")
        if "Assess the claim below" in prompt:
            return self.responses.get("verify", _json({"status": "unverified", "evidence": "", "sources": [], "notes": ""}))
        if "Produce the FINAL answer" in prompt:
            return self.responses.get("synthesis", _json({
                "final_answer": "Final.", "confidence_score": 0.7,
                "confidence_rationale": "ok", "caveats": [],
            }))
        # Default = draft stage
        return self.responses.get("draft", "Draft answer.")


def _json(obj) -> str:
    return json.dumps(obj)


@pytest.fixture
def scripted():
    return ScriptedProvider


@pytest.fixture
def jsonify():
    return _json
