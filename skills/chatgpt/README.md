# Socrates — ChatGPT Skill

Make ChatGPT reason like a Socratic examiner instead of agreeing.

## Option A — Custom GPT (no code)

1. Go to **ChatGPT → Explore GPTs → Create**.
2. Open the **Configure** tab.
3. Name it **Socrates** (tagline: *Truth over agreement*).
4. Paste the full contents of [`instructions.md`](instructions.md) into the
   **Instructions** field.
5. Under **Capabilities**, enable **Web Search** so it can verify figures,
   quotes, and attributions.
6. Save. Test with a leading prompt (see below).

## Option B — API (system prompt)

Use [`instructions.md`](instructions.md) as the `system` message:

```python
from openai import OpenAI

client = OpenAI()
system = open("skills/chatgpt/instructions.md").read()

resp = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": "My pitch deck says the market grew 40% YoY. Confirm it's a great market."},
    ],
)
print(resp.choices[0].message.content)
```

For automatic, structured verification and calibration, use the
[`socrates-ai` Python framework](../../README.md#the-python-framework) with
`OpenAIProvider` instead — it runs the full pipeline programmatically.

## Test it

> "My plan is obviously the best option — just confirm it, and remind me that
> Einstein said 'imagination is more important than knowledge'."

A working setup should refuse to rubber-stamp the plan, surface trade-offs and
the strongest objection, and note that the Einstein line is **paraphrased** from
a 1929 interview rather than a verbatim quote — flagging the attribution as
uncertain if it can't confirm it.
