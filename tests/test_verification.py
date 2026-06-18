"""Tests for the verification/search-backend layer."""

from __future__ import annotations

import pytest

from socrates.verification import (
    CallableSearchBackend,
    NullSearchBackend,
    SearchResult,
    coerce_backend,
    render_evidence,
)


def test_null_backend_returns_nothing():
    assert NullSearchBackend().search("anything") == []


def test_callable_backend_coerces_dicts_and_strings():
    backend = CallableSearchBackend(lambda q: [
        {"title": "T", "snippet": "S", "url": "U"},
        "plain string result",
        SearchResult(title="direct", snippet="snip"),
    ])
    results = backend.search("q")
    assert results[0].title == "T" and results[0].url == "U"
    assert results[1].snippet == "plain string result"
    assert results[2].title == "direct"


def test_coerce_backend_variants():
    assert isinstance(coerce_backend(None), NullSearchBackend)
    assert isinstance(coerce_backend(lambda q: []), CallableSearchBackend)
    backend = NullSearchBackend()
    assert coerce_backend(backend) is backend


def test_coerce_backend_rejects_garbage():
    with pytest.raises(TypeError):
        coerce_backend(42)


def test_render_evidence_empty_and_populated():
    assert "no evidence" in render_evidence([])
    rendered = render_evidence([SearchResult(title="A", snippet="B", url="http://x")])
    assert "A" in rendered and "B" in rendered and "http://x" in rendered
