"""Exception hierarchy for Socrates."""

from __future__ import annotations


class SocratesError(Exception):
    """Base class for all Socrates errors."""


class ProviderError(SocratesError):
    """Raised when an LLM provider cannot fulfil a request.

    Typically wraps the underlying SDK exception (missing dependency,
    authentication failure, network error, etc.).
    """


class ConfigurationError(SocratesError):
    """Raised when Socrates is misconfigured (e.g. missing API key)."""


class VerificationError(SocratesError):
    """Raised when the verification subsystem fails irrecoverably."""
