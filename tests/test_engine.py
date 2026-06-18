"""End-to-end pipeline tests using a scripted, offline provider."""

from __future__ import annotations

import json

import pytest

from socrates import Socrates
from socrates.engine import extract_json
from socrates.types import ConfidenceLevel, VerdictStatus


def test_reason_runs_full_pipeline(scripted, jsonify):
    provider = scripted({
        "draft": "Einstein definitely said it, full stop.",
        "critique": jsonify({
            "questions": ["Is the attribution verified?"],
            "weaknesses": ["States attribution as certain without a source."],
            "revised_answer": "The quote is commonly attributed to Einstein, but attribution is disputed.",
            "resolved": False,
        }),
        "adversarial": jsonify({
            "findings": ["Original draft was overconfident about attribution."],
            "disagreements": [
                {"premise": "Einstein said it", "objection": "No primary source", "suggestion": "Check Einstein archives"}
            ],
        }),
        "claims": jsonify([
            {"text": "Einstein said 'imagination is more important than knowledge'", "kind": "quote", "cited_source": None}
        ]),
        "verify": jsonify({
            "status": "misattributed",
            "evidence": "Phrase appears in a 1929 interview but wording differs.",
            "sources": ["https://example.org/einstein"],
            "notes": "Often paraphrased.",
        }),
        "synthesis": jsonify({
            "final_answer": "The attribution is plausible but not firmly documented.",
            "confidence_score": 0.8,
            "confidence_rationale": "Evidence is partial.",
            "caveats": ["Primary source not located."],
        }),
    })

    socrates = Socrates(provider=provider, critique_rounds=1, search=lambda q: [{"title": "t", "snippet": "s", "url": "u"}])
    result = socrates.reason("Did Einstein say imagination is more important than knowledge?")

    assert result.final_answer == "The attribution is plausible but not firmly documented."
    assert result.draft.startswith("Einstein definitely")
    assert len(result.critiques) == 1
    assert result.critiques[0].weaknesses
    assert result.adversarial_review
    assert result.disagreements and result.disagreements[0].premise == "Einstein said it"
    # One claim, misattributed -> flagged.
    assert len(result.verdicts) == 1
    assert result.verdicts[0].status == VerdictStatus.MISATTRIBUTED
    assert result.flagged_claims
    # Self-reported 0.8 minus misattribution (0.25) -> 0.55 -> MODERATE/LOW band.
    assert result.confidence.score < 0.8
    assert result.confidence.level in (ConfidenceLevel.MODERATE, ConfidenceLevel.LOW)
    assert any("misattributed" in c.lower() for c in result.confidence.caveats)


def test_revised_answer_propagates(scripted, jsonify):
    provider = scripted({
        "draft": "Original.",
        "critique": jsonify({"questions": [], "weaknesses": ["x"], "revised_answer": "Revised.", "resolved": True}),
        "claims": "[]",
        "synthesis": jsonify({"final_answer": "Revised.", "confidence_score": 0.6, "confidence_rationale": "", "caveats": []}),
    })
    socrates = Socrates(provider=provider, critique_rounds=2)
    result = socrates.reason("Q?")
    # Critique resolved on round 1, so only one round runs.
    assert len(result.critiques) == 1
    assert result.final_answer == "Revised."


def test_no_search_marks_claims_unverified(scripted, jsonify):
    provider = scripted({
        "draft": "GDP grew 12%.",
        "claims": jsonify([{"text": "GDP grew 12%", "kind": "figure", "cited_source": None}]),
        "synthesis": jsonify({"final_answer": "GDP figure uncertain.", "confidence_score": 0.9, "confidence_rationale": "", "caveats": []}),
    })
    socrates = Socrates(provider=provider, critique_rounds=0)  # no search backend
    result = socrates.reason("How much did GDP grow?")
    assert result.verdicts[0].status == VerdictStatus.UNVERIFIED
    # Unverified figure applies a small penalty.
    assert result.confidence.score < 0.9


def test_zero_rounds_skips_critique(scripted):
    provider = scripted({"draft": "A.", "claims": "[]"})
    socrates = Socrates(provider=provider, critique_rounds=0)
    result = socrates.reason("Q?")
    assert result.critiques == []


def test_no_verify_skips_claims(scripted, jsonify):
    provider = scripted({"draft": "A.", "synthesis": jsonify({"final_answer": "A.", "confidence_score": 0.5, "confidence_rationale": "", "caveats": []})})
    socrates = Socrates(provider=provider, critique_rounds=0, verify_claims=False)
    result = socrates.reason("Q?")
    assert result.verdicts == []


def test_empty_question_raises(scripted):
    socrates = Socrates(provider=scripted({}), critique_rounds=0)
    with pytest.raises(ValueError):
        socrates.reason("   ")


def test_negative_rounds_raises(scripted):
    with pytest.raises(ValueError):
        Socrates(provider=scripted({}), critique_rounds=-1)


def test_result_serialisation(scripted, jsonify):
    provider = scripted({"draft": "A.", "claims": "[]", "synthesis": jsonify({"final_answer": "A.", "confidence_score": 0.7, "confidence_rationale": "r", "caveats": ["c"]})})
    result = Socrates(provider=provider, critique_rounds=0).reason("Q?")
    d = result.to_dict()
    assert json.dumps(d)  # round-trips
    md = result.to_markdown()
    assert "# Socrates report" in md
    assert "Confidence" in md


@pytest.mark.parametrize(
    "text,expected",
    [
        ('{"a": 1}', {"a": 1}),
        ("```json\n{\"a\": 2}\n```", {"a": 2}),
        ("prose before {\"a\": 3} prose after", {"a": 3}),
        ("[1, 2, 3]", [1, 2, 3]),
        ("not json at all", None),
        ("", None),
    ],
)
def test_extract_json(text, expected):
    assert extract_json(text) == expected
