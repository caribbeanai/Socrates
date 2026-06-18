"""Confidence calibration.

The model reports a self-assessed confidence during synthesis. We then
adjust it downward in light of objective signals from the pipeline — refuted
or misattributed claims, unresolved critiques, unverified figures — so the
final number reflects the evidence, not just the model's mood.
"""

from __future__ import annotations

from .types import (
    ClaimVerdict,
    Confidence,
    ConfidenceLevel,
    Critique,
    VerdictStatus,
)

# Per-signal penalties applied to the model's self-reported score.
_PENALTY = {
    VerdictStatus.REFUTED: 0.30,
    VerdictStatus.MISATTRIBUTED: 0.25,
    VerdictStatus.UNCERTAIN: 0.10,
    VerdictStatus.UNVERIFIED: 0.05,
}
_UNRESOLVED_CRITIQUE_PENALTY = 0.05


def calibrate(
    self_reported: float,
    rationale: str,
    caveats: list[str],
    verdicts: list[ClaimVerdict],
    critiques: list[Critique],
) -> Confidence:
    """Combine the model's self-assessment with objective pipeline signals.

    Args:
        self_reported: The model's own 0.0–1.0 confidence from synthesis.
        rationale: The model's stated reason for that confidence.
        caveats: Caveats surfaced during synthesis.
        verdicts: Results of claim verification.
        critiques: The recursive self-critique trail.

    Returns:
        A calibrated :class:`Confidence`.
    """
    score = _clamp(self_reported)
    extra_caveats: list[str] = []

    for verdict in verdicts:
        penalty = _PENALTY.get(verdict.status, 0.0)
        if penalty:
            score -= penalty
        if verdict.status == VerdictStatus.REFUTED:
            extra_caveats.append(
                f"A claim was refuted by evidence: {verdict.claim.text}"
            )
        elif verdict.status == VerdictStatus.MISATTRIBUTED:
            extra_caveats.append(
                f"A claim appears misattributed: {verdict.claim.text}"
            )

    unresolved = [c for c in critiques if not c.resolved and c.weaknesses]
    if unresolved:
        score -= _UNRESOLVED_CRITIQUE_PENALTY * min(len(unresolved), 3)
        extra_caveats.append(
            f"{len(unresolved)} self-critique round(s) raised unresolved concerns."
        )

    score = _clamp(score)
    all_caveats = list(dict.fromkeys([*caveats, *extra_caveats]))  # de-dupe, keep order
    return Confidence(
        score=score,
        level=ConfidenceLevel.from_score(score),
        rationale=rationale,
        caveats=all_caveats,
    )


def _clamp(value: float) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 0.3
    return max(0.0, min(1.0, v))
