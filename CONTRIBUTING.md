# Contributing to Socrates

Thanks for your interest in Socrates.

## Maintainership

Socrates is authored and maintained by **Adrian Dunkley**
([@caribbeanai](https://github.com/caribbeanai) · <https://adriandunkley.net>).


You are very welcome to:

- **Open an issue** to report a bug, a misquote/misattribution the verifier
  missed, or a sycophancy failure mode.
- **Start a discussion** to propose an idea.

Pull requests from others are not being merged at this time — the project is
intentionally single-maintainer. If you have a fix in mind, please open an
issue describing it; Adrian will implement it (with credit).

## Development setup

```bash
git clone https://github.com/caribbeanai/socrates.git
cd socrates
pip install -e ".[all,dev]"
```

## Quality gates

All of these must pass before a change lands:

```bash
pytest            # offline test suite — no API keys or network required
ruff check .      # lint
ruff format .     # format (optional but encouraged)
mypy              # type-check
```

## Principles

When extending Socrates, keep faith with the method:

1. **Truth over agreement** -> features should make answers more honest, not
   more agreeable.
2. **No silent trust** -> never let an unverified figure, quote, or attribution
   be presented as confirmed.
3. **Calibration is objective** -> confidence should respond to evidence, not
   tone.
4. **Light dependencies** -> the core stays dependency-free; provider SDKs are
   optional extras and must be imported lazily.
5. **Provider-agnostic** -> anything stage-specific belongs in prompts or the
   engine, not in a provider.
