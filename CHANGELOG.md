# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project aims
to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-06-18

Initial release.

### Added
- **Python framework** (`socrates-ai`): a provider-agnostic anti-sycophancy
  engine with a five-stage pipeline — truth-seeking draft, recursive
  self-critique, adversarial review, evidence verification, and synthesis with
  confidence calibration and respectful disagreement.
- Providers for **Anthropic (Claude)**, **OpenAI (ChatGPT)**, and
  **Google (Gemini)**, each lazily importing its SDK, plus an `EchoProvider`
  for offline use.
- Pluggable evidence/search backends for verifying figures, quotes, and
  attributions (with graceful `unverified` degradation when none is supplied).
- Objective confidence calibration that penalises refuted/misattributed claims,
  unverified figures, and unresolved critiques.
- A `socrates` command-line interface (`python -m socrates`).
- **Claude Skill** (`skills/claude/SKILL.md`).
- **ChatGPT Skill** (`skills/chatgpt/instructions.md`).
- **Gemini Gem** (`skills/gemini/GEM.md`).
- Full offline test suite, CI, linting (ruff), and type-checking (mypy).

[0.1.0]: https://github.com/caribbeanai/socrates/releases/tag/v0.1.0
