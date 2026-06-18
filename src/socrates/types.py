"""Typed data structures returned by the Socrates pipeline.

These are plain dataclasses so they serialise cleanly to JSON and are easy
to assert on in tests. Nothing here imports a provider SDK.
"""

from __future__ import annotations

import enum
from dataclasses import asdict, dataclass, field
from typing import Any


class ClaimKind(str, enum.Enum):
    """The category of a checkable claim extracted from an answer."""

    FIGURE = "figure"          # a statistic, number, date, measurement
    QUOTE = "quote"            # a direct quotation attributed to someone
    ATTRIBUTION = "attribution"  # who said/did/wrote something
    FACT = "fact"              # a general factual assertion
    OTHER = "other"


class VerdictStatus(str, enum.Enum):
    """The outcome of verifying a single claim."""

    VERIFIED = "verified"          # corroborated by evidence
    REFUTED = "refuted"            # contradicted by evidence (misquote, etc.)
    MISATTRIBUTED = "misattributed"  # real, but wrongly attributed
    UNVERIFIED = "unverified"      # could not be checked (no evidence found)
    UNCERTAIN = "uncertain"        # evidence is mixed or inconclusive


class ConfidenceLevel(str, enum.Enum):
    """A coarse, human-readable confidence band."""

    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    SPECULATIVE = "speculative"

    @classmethod
    def from_score(cls, score: float) -> ConfidenceLevel:
        """Map a 0.0–1.0 score onto a confidence band."""
        if score >= 0.85:
            return cls.HIGH
        if score >= 0.6:
            return cls.MODERATE
        if score >= 0.35:
            return cls.LOW
        return cls.SPECULATIVE


#: Markers used when rendering verdicts to Markdown.
_VERDICT_MARKER: dict[VerdictStatus, str] = {
    VerdictStatus.VERIFIED: "✅",
    VerdictStatus.REFUTED: "❌",
    VerdictStatus.MISATTRIBUTED: "❌",
    VerdictStatus.UNCERTAIN: "⚠️",
    VerdictStatus.UNVERIFIED: "❔",
}


@dataclass
class Claim:
    """A discrete, checkable assertion lifted out of a draft answer."""

    text: str
    kind: ClaimKind = ClaimKind.FACT
    cited_source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"text": self.text, "kind": self.kind.value, "cited_source": self.cited_source}


@dataclass
class ClaimVerdict:
    """The result of checking one :class:`Claim`."""

    claim: Claim
    status: VerdictStatus
    evidence: str = ""
    sources: list[str] = field(default_factory=list)
    notes: str = ""

    @property
    def is_problem(self) -> bool:
        """True if this verdict should make us less confident."""
        return self.status in (
            VerdictStatus.REFUTED,
            VerdictStatus.MISATTRIBUTED,
            VerdictStatus.UNCERTAIN,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim.to_dict(),
            "status": self.status.value,
            "evidence": self.evidence,
            "sources": list(self.sources),
            "notes": self.notes,
        }


@dataclass
class Critique:
    """One round of recursive Socratic self-critique."""

    round: int
    questions: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    revised_answer: str | None = None
    resolved: bool = False  # True when the critic finds no further substantive issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "round": self.round,
            "questions": list(self.questions),
            "weaknesses": list(self.weaknesses),
            "revised_answer": self.revised_answer,
            "resolved": self.resolved,
        }


@dataclass
class Disagreement:
    """A point where Socrates respectfully pushes back on the user."""

    premise: str        # the user assumption being challenged
    objection: str      # why it may not hold
    suggestion: str = ""  # what to consider instead

    def to_dict(self) -> dict[str, Any]:
        return {"premise": self.premise, "objection": self.objection, "suggestion": self.suggestion}


@dataclass
class Confidence:
    """Calibrated confidence in the final answer."""

    score: float                 # 0.0–1.0
    level: ConfidenceLevel
    rationale: str = ""
    caveats: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 3),
            "level": self.level.value,
            "rationale": self.rationale,
            "caveats": list(self.caveats),
        }


@dataclass
class SocratesResult:
    """The full, auditable output of a Socrates reasoning run."""

    question: str
    draft: str
    final_answer: str
    confidence: Confidence
    critiques: list[Critique] = field(default_factory=list)
    adversarial_review: list[str] = field(default_factory=list)
    verdicts: list[ClaimVerdict] = field(default_factory=list)
    disagreements: list[Disagreement] = field(default_factory=list)

    @property
    def flagged_claims(self) -> list[ClaimVerdict]:
        """Claims that were refuted, misattributed, or are uncertain."""
        return [v for v in self.verdicts if v.is_problem]

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "draft": self.draft,
            "final_answer": self.final_answer,
            "confidence": self.confidence.to_dict(),
            "critiques": [c.to_dict() for c in self.critiques],
            "adversarial_review": list(self.adversarial_review),
            "verdicts": [v.to_dict() for v in self.verdicts],
            "disagreements": [d.to_dict() for d in self.disagreements],
        }

    def to_markdown(self) -> str:
        """Render a human-readable report of the whole run."""
        lines: list[str] = []
        lines.append("# Socrates report\n")
        lines.append(f"**Question:** {self.question}\n")
        lines.append("## Answer\n")
        lines.append(self.final_answer + "\n")
        c = self.confidence
        lines.append("## Confidence\n")
        lines.append(f"**{c.level.value.upper()}** ({c.score:.0%}) — {c.rationale}")
        for caveat in c.caveats:
            lines.append(f"- ⚠️ {caveat}")
        lines.append("")
        if self.disagreements:
            lines.append("## Respectful disagreement\n")
            for d in self.disagreements:
                lines.append(f"- **Premise:** {d.premise}\n  - Objection: {d.objection}")
                if d.suggestion:
                    lines.append(f"  - Consider: {d.suggestion}")
            lines.append("")
        if self.verdicts:
            lines.append("## Claim verification\n")
            for v in self.verdicts:
                marker = _VERDICT_MARKER.get(v.status, "•")
                lines.append(f"- {marker} *{v.claim.text}* — **{v.status.value}**")
                if v.evidence:
                    lines.append(f"  - {v.evidence}")
                for src in v.sources:
                    lines.append(f"  - source: {src}")
            lines.append("")
        if self.critiques:
            lines.append("## Self-critique trail\n")
            for crit in self.critiques:
                lines.append(f"### Round {crit.round}")
                for q in crit.questions:
                    lines.append(f"- ❓ {q}")
                for w in crit.weaknesses:
                    lines.append(f"- 🔧 {w}")
                lines.append("")
        return "\n".join(lines).strip() + "\n"

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return (
            f"SocratesResult(confidence={self.confidence.level.value}, "
            f"critiques={len(self.critiques)}, verdicts={len(self.verdicts)}, "
            f"flagged={len(self.flagged_claims)})"
        )


def _dataclass_to_dict(obj: Any) -> Any:  # pragma: no cover - utility
    """Fallback serialiser used by tests/tools."""
    return asdict(obj)
