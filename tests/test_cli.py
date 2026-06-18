"""Tests for the CLI wiring (offline, via the echo provider)."""

from __future__ import annotations

import json

from socrates import cli


def test_cli_echo_runs(capsys):
    rc = cli.main(["--provider", "echo", "--rounds", "0", "--no-verify", "Hello?"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Socrates report" in out


def test_cli_json_output(capsys):
    rc = cli.main(["--provider", "echo", "--rounds", "0", "--no-verify", "--json", "Q?"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["question"] == "Q?"
    assert "confidence" in payload


def test_cli_reads_stdin(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", _FakeStdin("piped question"))
    rc = cli.main(["--provider", "echo", "--rounds", "0", "--no-verify"])
    assert rc == 0
    assert "Socrates report" in capsys.readouterr().out


class _FakeStdin:
    def __init__(self, text):
        self._text = text

    def read(self):
        return self._text
