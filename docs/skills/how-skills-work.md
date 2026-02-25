# How Skills Work

This document explains the OpenClaw skill system for any agent or developer reading this. Understanding skills is essential to knowing how Eva interacts with the options toolkit.

---

## What Is a Skill?

A skill is a packaged capability for an OpenClaw agent. It consists of a single `SKILL.md` file that tells the agent:
1. **When** to activate (trigger phrases in the description)
2. **What** to do (instructions in the body)

Skills live in a directory structure:
```
~/.openclaw/workspace/skills/{skill-name}/SKILL.md
```

---

## SKILL.md Anatomy

A SKILL.md file has two parts:

### 1. YAML Frontmatter

```yaml
---
name: stock-price
description: >
  Check current stock prices and daily changes. Trigger when someone asks
  "what's X at", "price of X", "how's X doing", "check X price", or "X quote"
  where X is any stock ticker symbol. Returns formatted price data with
  change indicators.
metadata:
  openclaw:
    emoji: "📈"
    requires:
      bins: ["python3"]
---
```

| Field | Purpose |
|-------|---------|
| `name` | Unique skill identifier |
| `description` | ~100 words that are ALWAYS in the agent's context. This is how the agent knows when to activate the skill. |
| `metadata.openclaw.emoji` | Display emoji |
| `metadata.openclaw.requires.bins` | Binary dependencies that must be on PATH |

### 2. Markdown Body

The body contains detailed instructions that are loaded ONLY when the skill is triggered. This keeps the agent's base context small.

```markdown
## Instructions

When triggered, run the following command:

\`\`\`bash
python3 {baseDir}/../../options-toolkit/toolkit.py price --ticker {TICKER}
\`\`\`

Replace {TICKER} with the ticker symbol from the user's message.
Post the output directly to the channel.
```

---

## Progressive Disclosure

This is the key design principle of skills:

| Component | When Loaded | Size Target |
|-----------|-------------|-------------|
| `description` | ALWAYS in agent context | ~100 words |
| Body (instructions) | Only when triggered | <5,000 words |

The `description` acts as a trigger — the agent reads all skill descriptions to decide which skill (if any) matches the user's request. Once a skill is activated, the full body is loaded and the agent follows its instructions.

This means:
- 5 skill descriptions = ~500 words always in context (acceptable)
- Full instructions only loaded when needed (efficient)

---

## Three Tiers of Skills

OpenClaw discovers skills from three locations, in order of precedence:

| Tier | Location | Precedence | Description |
|------|----------|------------|-------------|
| Workspace | `~/.openclaw/workspace/skills/` | Highest | User-created, project-specific |
| Managed | `~/.openclaw/skills/` | Medium | Installed via openclaw commands |
| Bundled | `(openclaw install)/skills/` | Lowest | Shipped with openclaw (~52 skills) |

Our options toolkit skills go in the **workspace** tier since they're project-specific.

If two skills have the same name, the higher-precedence one wins.

---

## The `{baseDir}` Variable

In skill body instructions, `{baseDir}` resolves to the skill's own directory at runtime:

```
Skill file: ~/.openclaw/workspace/skills/stock-price/SKILL.md
{baseDir} = ~/.openclaw/workspace/skills/stock-price/
```

This allows skills to reference their own files or navigate to other parts of the workspace using relative paths:

```bash
python3 {baseDir}/../../options-toolkit/toolkit.py price --ticker IWM
#       ^^^^^^^^ = skills/stock-price/
#       ../../   = workspace/
#       options-toolkit/toolkit.py
```

---

## The `exec` Tool

Eva uses the `exec` tool to run shell commands. When a skill says "run this command," Eva calls:

```
exec: python3 ~/.openclaw/workspace/options-toolkit/toolkit.py price --ticker IWM
```

Behavior:
- Command runs on the host system directly
- Working directory is the workspace
- Timeout: 1800 seconds (30 minutes)
- stdout is captured and returned to Eva
- stderr is also captured (Eva can see errors)
- Exit code is returned

Eva then takes the stdout and posts it to the channel (or processes it according to skill instructions).

---

## How the Agent Decides to Activate a Skill

1. User sends a message (e.g., "what's IWM at?")
2. Agent reads all skill descriptions in its context
3. Agent matches the message against trigger phrases in descriptions
4. If a match is found, agent loads the skill body
5. Agent follows the instructions in the body
6. Agent captures output and responds

The agent uses natural language understanding — it doesn't need exact trigger phrase matches. "How's IWM doing today?" would match "how's X doing" in the stock-price skill description.

---

## Skill Design Guidelines for This Project

1. **One skill per toolkit subcommand** — clean separation
2. **Description focuses on trigger phrases** — what the user says to activate
3. **Body focuses on execution** — what command to run, how to handle output
4. **Always pass `--force` for report** — interactive requests should bypass market hours
5. **Handle multi-chunk output** — report skill instructs Eva to split at `---SPLIT---`
6. **Extract ticker from user message** — Eva parses the ticker symbol from natural language

---

## Ticker Extraction

Skills instruct Eva to extract the ticker symbol from the user's message:

```
User: "what's the play on IWM?"
Eva extracts: TICKER = IWM

User: "run the report for SPY"
Eva extracts: TICKER = SPY

User: "how's AAPL doing?"
Eva extracts: TICKER = AAPL
```

If the user doesn't specify a ticker, Eva should ask: "Which ticker do you want me to check?"
