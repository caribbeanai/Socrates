"""Tests for provider plumbing using injected fake SDK clients.

These verify request shaping and response parsing without importing real SDKs.
"""

from __future__ import annotations

import pytest

from socrates.exceptions import ProviderError
from socrates.providers import EchoProvider
from socrates.providers.anthropic import AnthropicProvider
from socrates.providers.openai import OpenAIProvider


# --- Anthropic ------------------------------------------------------------
class _Block:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class _Resp:
    def __init__(self, text):
        self.content = [_Block(text)]


class _FakeAnthropic:
    def __init__(self):
        self.captured = None
        self.messages = self

    def create(self, **kwargs):
        self.captured = kwargs
        return _Resp("hello from claude")


def test_anthropic_request_and_parse():
    fake = _FakeAnthropic()
    provider = AnthropicProvider(client=fake)
    out = provider.complete("SYS", "PROMPT", max_tokens=123)
    assert out == "hello from claude"
    assert fake.captured["model"] == "claude-opus-4-8"
    assert fake.captured["system"] == "SYS"
    assert fake.captured["max_tokens"] == 123
    assert fake.captured["thinking"] == {"type": "adaptive"}
    assert fake.captured["messages"] == [{"role": "user", "content": "PROMPT"}]


def test_anthropic_wraps_errors():
    class Boom:
        messages = property(lambda self: self)

        def create(self, **kwargs):
            raise RuntimeError("kaboom")

    provider = AnthropicProvider(client=Boom())
    with pytest.raises(ProviderError):
        provider.complete("s", "p")


# --- OpenAI ---------------------------------------------------------------
class _Msg:
    def __init__(self, content):
        self.message = type("M", (), {"content": content})


class _OAResp:
    def __init__(self, content):
        self.choices = [_Msg(content)]


class _FakeOpenAI:
    def __init__(self):
        self.captured = None
        self.chat = type("C", (), {"completions": self})()

    def create(self, **kwargs):
        self.captured = kwargs
        return _OAResp("hi from gpt")


def test_openai_request_and_parse():
    fake = _FakeOpenAI()
    provider = OpenAIProvider(client=fake)
    out = provider.complete("SYS", "PROMPT")
    assert out == "hi from gpt"
    roles = [m["role"] for m in fake.captured["messages"]]
    assert roles == ["system", "user"]


# --- Echo -----------------------------------------------------------------
def test_echo_provider_default_and_callable():
    assert EchoProvider().complete("s", "p") == ""
    echo = EchoProvider(responder=lambda system, prompt: f"{system}|{prompt}")
    assert echo.complete("S", "P") == "S|P"
