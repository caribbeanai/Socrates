"""OpenAI (ChatGPT) provider.

Requires the ``openai`` package: ``pip install "socrates-ai[openai]"``.
"""

from __future__ import annotations

import os

from ..exceptions import ConfigurationError, ProviderError
from .base import Provider

DEFAULT_MODEL = "gpt-4o"


class OpenAIProvider(Provider):
    """Calls the OpenAI Chat Completions API."""

    name = "openai"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        *,
        client=None,
    ):
        self.model = model
        if client is not None:
            self._client = client
            return
        try:
            import openai  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            raise ConfigurationError(
                "The 'openai' package is required for OpenAIProvider. "
                'Install it with: pip install "socrates-ai[openai]"'
            ) from exc
        key = api_key or os.environ.get("OPENAI_API_KEY")
        self._client = openai.OpenAI(api_key=key) if key else openai.OpenAI()

    def complete(self, system: str, prompt: str, *, max_tokens: int = 4096) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            )
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"OpenAI request failed: {exc}") from exc
        choices = getattr(response, "choices", None) or []
        if not choices:
            return ""
        return (choices[0].message.content or "").strip()
