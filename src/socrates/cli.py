"""Command-line interface for Socrates.

Examples::

    socrates "Did Einstein say imagination is more important than knowledge?"
    socrates --provider openai --rounds 3 "Is my startup idea good?" --context "$(cat pitch.txt)"
    echo "Review this claim: the GDP grew 12% last year" | socrates --json
"""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .engine import Socrates
from .exceptions import SocratesError

_PROVIDERS = ("anthropic", "openai", "gemini", "echo")


def _build_provider(name: str, model: str | None):
    if name == "anthropic":
        from .providers import AnthropicProvider

        return AnthropicProvider(model=model) if model else AnthropicProvider()
    if name == "openai":
        from .providers import OpenAIProvider

        return OpenAIProvider(model=model) if model else OpenAIProvider()
    if name == "gemini":
        from .providers import GeminiProvider

        return GeminiProvider(model=model) if model else GeminiProvider()
    if name == "echo":
        from .providers import EchoProvider

        return EchoProvider()
    raise SocratesError(f"Unknown provider: {name}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="socrates",
        description="Stop agreeing. Start reasoning. Reduce AI sycophancy with "
        "recursive critique, adversarial review, and evidence verification.",
    )
    parser.add_argument("question", nargs="?", help="The question (or '-' / omit to read stdin).")
    parser.add_argument(
        "-p", "--provider", choices=_PROVIDERS, default="anthropic",
        help="LLM backend (default: anthropic).",
    )
    parser.add_argument("-m", "--model", default=None, help="Override the provider's default model.")
    parser.add_argument(
        "-r", "--rounds", type=int, default=2, help="Self-critique rounds (default: 2).",
    )
    parser.add_argument("--context", default=None, help="Extra context for the question.")
    parser.add_argument("--no-verify", action="store_true", help="Skip claim verification.")
    parser.add_argument("--json", action="store_true", help="Emit the full result as JSON.")
    parser.add_argument("--version", action="version", version=f"socrates {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    question = args.question
    if not question or question == "-":
        question = sys.stdin.read().strip()
    if not question:
        parser.error("no question provided (pass an argument or pipe via stdin)")

    try:
        provider = _build_provider(args.provider, args.model)
        socrates = Socrates(
            provider=provider,
            critique_rounds=args.rounds,
            verify_claims=not args.no_verify,
        )
        result = socrates.reason(question, context=args.context)
    except SocratesError as exc:
        print(f"socrates: error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:  # pragma: no cover
        return 130

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(result.to_markdown())
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
