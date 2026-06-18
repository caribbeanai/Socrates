"""Tests for confidence calibration."""

from __future__ import annotations

from socrates.calibration import calibrate
from socrates.types import (
    Claim,
    ClaimVerdict,
    ConfidenceLevel,
    Critique,
    VerdictStatus,
)


def _verdict(status: VerdictStatus) -> ClaimVerdict:
    return ClaimVerdict(claim=Claim(text="x"), status=status)


def test_clean_run_keeps_score():
    conf = calibrate(0.9, "solid", [], [_verdict(VerdictStatus.VERIFIED)], [])
    assert conf.score == 0.9
    assert conf.level == ConfidenceLevel.HIGH


def test_refuted_claim_penalises_and_caveats():
    conf = calibrate(0.9, "", [], [_verdict(VerdictStatus.REFUTED)], [])
    assert abs(conf.score - 0.6) < 1e-9
    assert any("refuted" in c.lower() for c in conf.caveats)


def test_misattribution_penalty():
    conf = calibrate(0.8, "", [], [_verdict(VerdictStatus.MISATTRIBUTED)], [])
    assert abs(conf.score - 0.55) < 1e-9


def test_unresolved_critiques_penalise():
    crits = [Critique(round=1, weaknesses=["w"], resolved=False)]
    conf = calibrate(0.7, "", [], [], crits)
    assert conf.score < 0.7
    assert any("unresolved" in c.lower() for c in conf.caveats)


def test_score_clamped_to_unit_interval():
    assert calibrate(5.0, "", [], [], []).score == 1.0
    conf = calibrate(0.1, "", [], [_verdict(VerdictStatus.REFUTED)], [])
    assert conf.score == 0.0


def test_bad_score_defaults_gracefully():
    conf = calibrate("not-a-number", "", [], [], [])  # type: ignore[arg-type]
    assert 0.0 <= conf.score <= 1.0


def test_level_bands():
    assert ConfidenceLevel.from_score(0.95) == ConfidenceLevel.HIGH
    assert ConfidenceLevel.from_score(0.7) == ConfidenceLevel.MODERATE
    assert ConfidenceLevel.from_score(0.4) == ConfidenceLevel.LOW
    assert ConfidenceLevel.from_score(0.1) == ConfidenceLevel.SPECULATIVE
