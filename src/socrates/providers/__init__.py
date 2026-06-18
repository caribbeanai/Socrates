"""Pluggable LLM providers for Socrates.

Concrete providers lazily import their SDKs, so importing this package never
forces ``anthropic``/``openai``/``google-generativeai`` to be installed.
"""

from __future__ import annotations

from .anthropic import AnthropicProvider
from .base import EchoProvider, Provider
from .gemini import GeminiProvider
from .openai import OpenAIProvider

__all__ = [
    "Provider",
    "EchoProvider",
    "AnthropicProvider",
    "OpenAIProvider",
    "GeminiProvider",
]
