"""Provider abstraction.

A provider is anything that can turn a system prompt + user prompt into a
text completion. Concrete providers lazily import their SDK so that the base
``socrates`` install carries no heavy dependencies.
"""

from __future__ import annotations

import abc


class Provider(abc.ABC):
    """Abstract base class for LLM backends."""

    #: Human-readable provider name, used in logs and errors.
    name: str = "provider"

    @abc.abstractmethod
    def complete(self, system: str, prompt: str, *, max_tokens: int = 4096) -> str:
        """Return the model's text completion for ``prompt``.

        Args:
            system: The system prompt establishing the Socrates persona.
            prompt: The user-turn instruction for this stage.
            max_tokens: Upper bound on output tokens.

        Returns:
            The completion text (never ``None``; empty string on no content).
        """
        raise NotImplementedError


class EchoProvider(Provider):
    """A deterministic, dependency-free provider for tests and demos.

    It does not reason — it simply returns a canned or callable response. Use
    it to exercise the pipeline plumbing without spending tokens.
    """

    name = "echo"

    def __init__(self, responder=None):
        # responder: Optional[Callable[[str, str], str]]
        self._responder = responder

    def complete(self, system: str, prompt: str, *, max_tokens: int = 4096) -> str:
        if self._responder is not None:
            return self._responder(system, prompt)
        return ""
