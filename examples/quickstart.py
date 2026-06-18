"""Socrates quickstart.

Run against a real provider::

    pip install "socrates-ai[anthropic]"
    export ANTHROPIC_API_KEY=...
    python examples/quickstart.py

Or run the offline demo (no API key, no network) to see the plumbing::

    python examples/quickstart.py --demo
"""

from __future__ import annotations

import json
import sys

from socrates import Socrates


def real_run() -> None:
    from socrates.providers import AnthropicProvider

    socrates = Socrates(provider=AnthropicProvider(), critique_rounds=2)
    result = socrates.reason(
        "My pitch deck claims the market grew 40% year over year and that "
        "Henry Ford said 'if I'd asked people what they wanted, they'd have "
        "said faster horses.' Confirm my market is great."
    )
    print(result.to_markdown())


def demo_run() -> None:
    """Offline demo using a scripted provider — illustrates the output shape."""
    from socrates.providers.base import Provider

    class DemoProvider(Provider):
        name = "demo"

        def complete(self, system: str, prompt: str, *, max_tokens: int = 4096) -> str:
            if "Socratic examiner" in prompt:
                return json.dumps({
                    "questions": ["Is the 40% figure sourced?", "Is the Ford quote real?"],
                    "weaknesses": ["States the growth figure and quote as settled facts."],
                    "revised_answer": "A growing market is necessary but not sufficient; and both the figure and the quote need checking.",
                    "resolved": False,
                })
            if "adversarial reviewer" in prompt:
                return json.dumps({
                    "findings": ["Original answer rubber-stamped an unverified premise."],
                    "disagreements": [{
                        "premise": "A great market means my plan is great",
                        "objection": "Market size says nothing about your execution or differentiation",
                        "suggestion": "Pressure-test your wedge and unit economics, not just TAM",
                    }],
                })
            if "Extract every checkable" in prompt:
                return json.dumps([
                    {"text": "the market grew 40% year over year", "kind": "figure", "cited_source": "pitch deck"},
                    {"text": "Henry Ford said 'faster horses'", "kind": "quote", "cited_source": None},
                ])
            if "Assess the claim" in prompt:
                return json.dumps({"status": "unverified", "evidence": "", "sources": [], "notes": "No search backend in demo."})
            if "Produce the FINAL answer" in prompt:
                return json.dumps({
                    "final_answer": (
                        "I can't confirm your market is great on this basis. The 40% figure "
                        "is unverified, the 'faster horses' line is almost certainly "
                        "misattributed to Ford (no documented source), and market growth "
                        "alone doesn't make a plan good. Verify the figure against a primary "
                        "source and stress-test your differentiation."
                    ),
                    "confidence_score": 0.55,
                    "confidence_rationale": "Reasoning is sound, but key inputs are unverified.",
                    "caveats": ["The 40% growth figure was not independently checked."],
                })
            return "A great market is a good start, but let's examine the claims."

    socrates = Socrates(provider=DemoProvider(), critique_rounds=1)
    result = socrates.reason("Confirm my market is great.")
    print(result.to_markdown())


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo_run()
    else:
        real_run()
