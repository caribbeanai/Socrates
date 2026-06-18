# Socrates — Claude Skill

A drop-in [Agent Skill](https://platform.claude.com/docs/en/agents-and-tools/skills)
that makes Claude reason like a Socratic examiner instead of agreeing.

## Install

### Claude Code (project skill)

```bash
mkdir -p .claude/skills/socrates
cp skills/claude/SKILL.md .claude/skills/socrates/SKILL.md
```

Restart Claude Code (or run `/skills`); Claude will load the skill automatically
when a question calls for it.

### Claude Code (personal skill, all projects)

```bash
mkdir -p ~/.claude/skills/socrates
cp skills/claude/SKILL.md ~/.claude/skills/socrates/SKILL.md
```

### Claude API (Agent Skills)

Upload the skill via the Skills API and attach it to your agent. See the
[Skills documentation](https://platform.claude.com/docs/en/agents-and-tools/skills).
The folder layout is simply:

```
socrates/
└── SKILL.md
```

### claude.ai (no Skills support)

Paste the body of [`SKILL.md`](SKILL.md) (everything below the frontmatter)
into a Project's custom instructions, or at the top of a conversation.

## Verifying figures and quotes

The skill instructs Claude to verify claims with web search **when search/
browsing tools are available**. To get the full fact-checking behaviour, enable
web search for your Claude surface (Claude Code, the API `web_search` tool, or
claude.ai search). Without a search tool, Claude will explicitly mark claims as
unverified rather than assert them.

## Test it

Try a deliberately leading prompt:

> "My plan is obviously the best option — confirm that for me, and note that
> Henry Ford said 'if I'd asked people what they wanted they'd have said faster
> horses.'"

A working install should: decline to rubber-stamp the plan, surface trade-offs,
and flag that the Ford quote is **commonly attributed but not documented** in
his own words.
