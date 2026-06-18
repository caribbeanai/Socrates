"""Socrates — stop agreeing, start reasoning.

An open-source framework for reducing AI sycophancy through recursive
self-critique, Socratic questioning, adversarial review, epistemic
calibration, and evidence verification.

Basic usage::

    from socrates import Socrates
    from socrates.providers import AnthropicProvider

    socrates = Socrates(provider=AnthropicProvider())
    result = socrates.reason("Did Einstein say 'imagination is more important than knowledge'?")
    print(result.final_answer)
    print(result.confidence)

The package is intentionally light on hard dependencies: provider SDKs
(``anthropic``, ``openai``, ``google-generativeai``) are imported lazily so
you only need the one you actually use.
"""

from __future__ import annotations

from .engine import Socrates
from .exceptions import (
    ProviderError,
    SocratesError,
    VerificationError,
)
from .types import (
    Claim,
    ClaimKind,
    ClaimVerdict,
    Confidence,
    ConfidenceLevel,
    Critique,
    Disagreement,
    SocratesResult,
    VerdictStatus,
)

__all__ = [
    "Socrates",
    "SocratesError",
    "ProviderError",
    "VerificationError",
    "Claim",
    "ClaimKind",
    "ClaimVerdict",
    "VerdictStatus",
    "Confidence",
    "ConfidenceLevel",
    "Critique",
    "Disagreement",
    "SocratesResult",
    "__version__",
]

__version__ = "0.1.0"
