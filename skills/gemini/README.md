# Socrates — Gemini Gem

Make Gemini reason like a Socratic examiner instead of agreeing.

## Create the Gem

1. Open [Gemini](https://gemini.google.com) → **Gems** → **New Gem**
   (Gem manager). Available on the web and in the Gemini apps.
2. **Name:** `Socrates`.
3. Paste the **Instructions** section of [`GEM.md`](GEM.md) into the
   *Instructions* box.
4. Save and start a chat with the Gem.

Gemini's built-in **Google Search grounding** lets the Gem verify figures,
quotes, and attributions automatically — keep grounding enabled for the full
fact-checking behaviour.

## API alternative

To run the same protocol programmatically (with structured verification and
calibration), use the [`socrates-ai` Python framework](../../README.md#the-python-framework)
with `GeminiProvider`:

```python
from socrates import Socrates
from socrates.providers import GeminiProvider

socrates = Socrates(provider=GeminiProvider(model="gemini-1.5-pro"))
print(socrates.reason("Is this obviously a great market?").to_markdown())
```

## Test it

> "Everyone agrees my approach is best — confirm it, and cite that Marie
> Antoinette said 'let them eat cake'."

A working Gem should decline to simply agree, surface the strongest objections,
and flag that the Marie Antoinette quote is **misattributed** — there is no
evidence she said it.
