"""Google Gemini provider.

Requires the ``google-generativeai`` package:
``pip install "socrates-ai[gemini]"``.
"""

from __future__ import annotations

import os

from ..exceptions import ConfigurationError, ProviderError
from .base import Provider

DEFAULT_MODEL = "gemini-1.5-pro"


class GeminiProvider(Provider):
    """Calls the Google Generative AI (Gemini) API."""

    name = "gemini"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        *,
        client=None,
    ):
        self.model = model
        if client is not None:
            self._model_client = client
            return
        try:
            import google.generativeai as genai
        except ImportError as exc:  # pragma: no cover
            raise ConfigurationError(
                "The 'google-generativeai' package is required for GeminiProvider. "
                'Install it with: pip install "socrates-ai[gemini]"'
            ) from exc
        key = api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise ConfigurationError(
                "Set GOOGLE_API_KEY (or GEMINI_API_KEY) for GeminiProvider."
            )
        genai.configure(api_key=key)
        self._model_client = genai.GenerativeModel(model)

    def complete(self, system: str, prompt: str, *, max_tokens: int = 4096) -> str:
        # Gemini has no dedicated system role on the basic API, so we prepend it.
        full_prompt = f"{system}\n\n{prompt}"
        try:
            response = self._model_client.generate_content(
                full_prompt,
                generation_config={"max_output_tokens": max_tokens},
            )
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"Gemini request failed: {exc}") from exc
        text = getattr(response, "text", None)
        return (text or "").strip()
