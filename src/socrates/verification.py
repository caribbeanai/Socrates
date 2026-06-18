"""Evidence retrieval for claim verification.

Socrates verifies figures, quotes, and attributions against external
evidence. *How* evidence is fetched is pluggable: pass any object with a
``search(query) -> list[SearchResult]`` method (or a plain callable) as the
``search`` argument to :class:`socrates.Socrates`.

If no search backend is supplied, verification degrades gracefully: every
checkable claim is marked ``unverified`` rather than silently trusted. This
is deliberate — an unchecked figure is not a confirmed figure.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class SearchResult:
    """A single piece of retrieved evidence."""

    title: str
    snippet: str
    url: str = ""

    def render(self) -> str:
        head = self.title or self.url or "result"
        body = self.snippet.strip()
        tail = f" ({self.url})" if self.url else ""
        return f"- {head}{tail}: {body}"


@runtime_checkable
class SearchBackend(Protocol):
    """Anything that can return evidence for a query."""

    def search(self, query: str) -> Sequence[SearchResult]:  # pragma: no cover - protocol
        ...


class NullSearchBackend:
    """A backend that returns nothing. Forces all claims to ``unverified``."""

    def search(self, query: str) -> list[SearchResult]:
        return []


class CallableSearchBackend:
    """Wraps a ``Callable[[str], Sequence[SearchResult | dict | str]]``.

    Accepts results as :class:`SearchResult`, dicts (``title``/``snippet``/
    ``url`` keys), or plain strings, so it is easy to plug in an existing
    search function, a Claude web-search tool result, or test fixtures.
    """

    def __init__(self, fn: Callable[[str], Sequence[object]]):
        self._fn = fn

    def search(self, query: str) -> list[SearchResult]:
        raw = self._fn(query) or []
        results: list[SearchResult] = []
        for item in raw:
            results.append(_coerce(item))
        return results


def _coerce(item: object) -> SearchResult:
    if isinstance(item, SearchResult):
        return item
    if isinstance(item, dict):
        return SearchResult(
            title=str(item.get("title", "")),
            snippet=str(item.get("snippet", item.get("content", ""))),
            url=str(item.get("url", "")),
        )
    return SearchResult(title="", snippet=str(item))


def coerce_backend(search: object) -> SearchBackend:
    """Normalise the ``search`` argument into a :class:`SearchBackend`."""
    if search is None:
        return NullSearchBackend()
    if isinstance(search, SearchBackend):
        return search
    if callable(search):
        return CallableSearchBackend(search)  # type: ignore[arg-type]
    raise TypeError(
        "search must be None, a SearchBackend (with a .search method), or a callable"
    )


def render_evidence(results: Sequence[SearchResult]) -> str:
    """Format search results for inclusion in a verification prompt."""
    if not results:
        return "(no evidence retrieved)"
    return "\n".join(r.render() for r in results)
