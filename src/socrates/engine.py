"""The Socrates reasoning engine.

Orchestrates the anti-sycophancy pipeline:

    draft → recursive self-critique → adversarial review
          → claim extraction → evidence verification
          → synthesis + calibration

Every stage is provider-agnostic; the only thing the engine needs is a
:class:`socrates.providers.base.Provider`.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from . import prompts
from .calibration import calibrate
from .providers.base import Provider
from .types import (
    Claim,
    ClaimKind,
    ClaimVerdict,
    Critique,
    Disagreement,
    SocratesResult,
    VerdictStatus,
)
from .verification import SearchBackend, coerce_backend, render_evidence

logger = logging.getLogger("socrates")

_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def extract_json(text: str) -> Any:
    """Best-effort extraction of a JSON value from a model response.

    Handles fenced code blocks, leading/trailing prose, and returns ``None``
    if nothing parseable is found (callers fall back to safe defaults).
    """
    if not text:
        return None
    # 1. Try a fenced ```json block.
    match = _JSON_FENCE.search(text)
    candidates = [match.group(1)] if match else []
    # 2. Try the raw text.
    candidates.append(text.strip())
    # 3. Try the first {...} or [...] span.
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        end = text.rfind(closer)
        if 0 <= start < end:
            candidates.append(text[start : end + 1])
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            continue
    logger.debug("Could not parse JSON from response: %s", text[:200])
    return None


class Socrates:
    """A Socratic reasoning wrapper around any LLM provider.

    Args:
        provider: The LLM backend that performs each stage.
        critique_rounds: Maximum rounds of recursive self-critique (>= 0).
        search: Optional evidence backend (object with ``.search`` or a
            callable). Without it, checkable claims are marked ``unverified``.
        verify_claims: If ``False``, skips claim extraction/verification.
        max_claims: Cap on the number of claims verified per run.
        max_tokens: Output token budget per stage.
    """

    def __init__(
        self,
        provider: Provider,
        *,
        critique_rounds: int = 2,
        search: object | None = None,
        verify_claims: bool = True,
        max_claims: int = 8,
        max_tokens: int = 4096,
    ):
        if critique_rounds < 0:
            raise ValueError("critique_rounds must be >= 0")
        self.provider = provider
        self.critique_rounds = critique_rounds
        self.verify_claims = verify_claims
        self.max_claims = max_claims
        self.max_tokens = max_tokens
        self.search: SearchBackend = coerce_backend(search)

    # -- public API --------------------------------------------------------
    def reason(self, question: str, *, context: str | None = None) -> SocratesResult:
        """Run the full pipeline and return an auditable result."""
        if not question or not question.strip():
            raise ValueError("question must be a non-empty string")

        draft = self._draft(question, context)
        answer = draft
        critiques = self._run_critiques(question, answer)
        if critiques and critiques[-1].revised_answer:
            answer = critiques[-1].revised_answer
        # Use the most recent revised answer across all rounds.
        for crit in critiques:
            if crit.revised_answer:
                answer = crit.revised_answer

        findings, disagreements = self._adversarial_review(question, answer)

        verdicts: list[ClaimVerdict] = []
        if self.verify_claims:
            claims = self._extract_claims(answer)
            verdicts = [self._verify_claim(c) for c in claims[: self.max_claims]]

        final_answer, conf_score, conf_rationale, caveats = self._synthesize(
            question, answer, findings, verdicts
        )

        confidence = calibrate(conf_score, conf_rationale, caveats, verdicts, critiques)

        return SocratesResult(
            question=question,
            draft=draft,
            final_answer=final_answer,
            confidence=confidence,
            critiques=critiques,
            adversarial_review=findings,
            verdicts=verdicts,
            disagreements=disagreements,
        )

    # -- pipeline stages ---------------------------------------------------
    def _draft(self, question: str, context: str | None) -> str:
        prompt = prompts.DRAFT_PROMPT.format(
            question=question, context_block=prompts.context_block(context)
        )
        return self._complete(prompt).strip()

    def _run_critiques(self, question: str, answer: str) -> list[Critique]:
        critiques: list[Critique] = []
        current = answer
        for i in range(self.critique_rounds):
            prompt = prompts.CRITIQUE_PROMPT.format(
                round_n=i + 1, question=question, answer=current
            )
            data = extract_json(self._complete(prompt)) or {}
            critique = Critique(
                round=i + 1,
                questions=_as_str_list(data.get("questions")),
                weaknesses=_as_str_list(data.get("weaknesses")),
                revised_answer=_as_opt_str(data.get("revised_answer")),
                resolved=bool(data.get("resolved", False)),
            )
            critiques.append(critique)
            if critique.revised_answer:
                current = critique.revised_answer
            if critique.resolved:
                break
        return critiques

    def _adversarial_review(
        self, question: str, answer: str
    ) -> tuple[list[str], list[Disagreement]]:
        prompt = prompts.ADVERSARIAL_PROMPT.format(question=question, answer=answer)
        data = extract_json(self._complete(prompt)) or {}
        findings = _as_str_list(data.get("findings"))
        disagreements: list[Disagreement] = []
        for d in data.get("disagreements") or []:
            if isinstance(d, dict) and d.get("premise"):
                disagreements.append(
                    Disagreement(
                        premise=str(d.get("premise", "")),
                        objection=str(d.get("objection", "")),
                        suggestion=str(d.get("suggestion", "")),
                    )
                )
        return findings, disagreements

    def _extract_claims(self, answer: str) -> list[Claim]:
        prompt = prompts.EXTRACT_CLAIMS_PROMPT.format(answer=answer)
        data = extract_json(self._complete(prompt))
        claims: list[Claim] = []
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict) or not item.get("text"):
                    continue
                claims.append(
                    Claim(
                        text=str(item["text"]),
                        kind=_as_kind(item.get("kind")),
                        cited_source=_as_opt_str(item.get("cited_source")),
                    )
                )
        return claims

    def _verify_claim(self, claim: Claim) -> ClaimVerdict:
        query = claim.text if not claim.cited_source else f"{claim.text} {claim.cited_source}"
        results = list(self.search.search(query))
        if not results:
            return ClaimVerdict(
                claim=claim,
                status=VerdictStatus.UNVERIFIED,
                notes="No evidence backend or no results; claim not independently checked.",
            )
        prompt = prompts.VERIFY_CLAIM_PROMPT.format(
            claim=claim.text, evidence=render_evidence(results)
        )
        data = extract_json(self._complete(prompt)) or {}
        return ClaimVerdict(
            claim=claim,
            status=_as_status(data.get("status")),
            evidence=str(data.get("evidence", "")),
            sources=_as_str_list(data.get("sources")),
            notes=str(data.get("notes", "")),
        )

    def _synthesize(
        self,
        question: str,
        answer: str,
        findings: list[str],
        verdicts: list[ClaimVerdict],
    ) -> tuple[str, float, str, list[str]]:
        prompt = prompts.SYNTHESIS_PROMPT.format(
            question=question,
            answer=answer,
            findings=_bullet(findings) or "(none)",
            verdicts=_render_verdicts(verdicts) or "(no claims checked)",
        )
        data = extract_json(self._complete(prompt)) or {}
        final_answer = _as_opt_str(data.get("final_answer")) or answer
        score = data.get("confidence_score", 0.5)
        rationale = str(data.get("confidence_rationale", ""))
        caveats = _as_str_list(data.get("caveats"))
        return final_answer, score, rationale, caveats

    # -- helpers -----------------------------------------------------------
    def _complete(self, prompt: str) -> str:
        return self.provider.complete(
            prompts.SYSTEM_PROMPT, prompt, max_tokens=self.max_tokens
        )


# --- module-level coercion helpers ----------------------------------------
def _as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(v) for v in value if v not in (None, "")]


def _as_opt_str(value: Any) -> str | None:
    if value in (None, "", "null"):
        return None
    return str(value)


def _as_kind(value: Any) -> ClaimKind:
    try:
        return ClaimKind(str(value).lower())
    except ValueError:
        return ClaimKind.FACT


def _as_status(value: Any) -> VerdictStatus:
    try:
        return VerdictStatus(str(value).lower())
    except ValueError:
        return VerdictStatus.UNVERIFIED


def _bullet(items: list[str]) -> str:
    return "\n".join(f"- {i}" for i in items)


def _render_verdicts(verdicts: list[ClaimVerdict]) -> str:
    lines = []
    for v in verdicts:
        lines.append(f"- [{v.status.value}] {v.claim.text}" + (f" — {v.evidence}" if v.evidence else ""))
    return "\n".join(lines)
