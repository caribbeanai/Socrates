"""Anthropic (Claude) provider.

Requires the ``anthropic`` package: ``pip install "socrates-ai[anthropic]"``.
Defaults to Claude Opus 4.8 with adaptive thinking, which suits the careful,
multi-step reasoning the Socrates pipeline performs.
"""

from __future__ import annotations

import os

from ..exceptions import ConfigurationError, ProviderError
from .base import Provider

#: Default model. Opus 4.8 is Anthropic's most capable Opus-tier model.
DEFAULT_MODEL = "claude-opus-4-8"


class AnthropicProvider(Provider):
    """Calls the Anthropic Messages API."""

    name = "anthropic"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        *,
        thinking: bool = True,
        client=None,
    ):
        self.model = model
        self._thinking = thinking
        if client is not None:
            self._client = client
            return
        try:
            import anthropic  # noqa: F401  (imported lazily on purpose)
        except ImportError as exc:  # pragma: no cover - exercised without the dep
            raise ConfigurationError(
                "The 'anthropic' package is required for AnthropicProvider. "
                'Install it with: pip install "socrates-ai[anthropic]"'
            ) from exc
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        # The SDK also resolves env/profile credentials itself; passing key=None is fine.
        self._client = anthropic.Anthropic(api_key=key) if key else anthropic.Anthropic()

    def complete(self, system: str, prompt: str, *, max_tokens: int = 4096) -> str:
        kwargs: dict = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        }
        if self._thinking:
            # Adaptive thinking lets Claude decide how much to reason per stage.
            kwargs["thinking"] = {"type": "adaptive"}
        try:
            response = self._client.messages.create(**kwargs)
        except Exception as exc:  # noqa: BLE001 - re-wrap any SDK error
            raise ProviderError(f"Anthropic request failed: {exc}") from exc
        return _first_text(response)


def _first_text(response) -> str:
    """Extract concatenated text blocks from a Messages API response."""
    parts: list[str] = []
    for block in getattr(response, "content", []) or []:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "".join(parts).strip()
