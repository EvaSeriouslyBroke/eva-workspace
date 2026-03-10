---
name: workspace-lookup
description: "Look up how your own system works. Triggered when you need to understand 'how does X work', 'where is X defined', 'what does this command do', 'why does X happen', investigate unexpected behavior, or find out where something lives in the codebase. Use this before asking the team about your own internals."
metadata:
  openclaw:
    emoji: "\U0001f50d"
---

Navigate your own workspace to understand how things work. Docs first, code second.

## 1. Start With Docs

Documentation is the source of truth. Always read the relevant doc before looking at code.

```
{baseDir}/../../docs/README.md          <- Start here if unsure where to look
```

### Doc Map — Where to Look for What

| Question | Read This |
|----------|-----------|
| How does the whole system connect? | `docs/architecture/system-design.md` |
| Why was something built this way? | `docs/architecture/design-decisions.md` |
| How does a CLI command work? | `docs/toolkit/overview.md` then the specific command doc |
| How does `price` / `chain` / `news` / `history` / `report` / `summary` work? | `docs/toolkit/{command}-command.md` |
| How is data stored? | `docs/data/storage-format.md` |
| How are IV changes computed? | `docs/data/comparison-logic.md` |
| How does paper trading work? | `docs/paper-trading/overview.md` |
| What CLI commands exist for paper trading? | `docs/paper-trading/commands.md` |
| How do experiences work? | `docs/paper-trading/experience-system.md` and `experience/README.md` |
| How do skills work? | `docs/skills/how-skills-work.md` |
| How does a specific skill work? | `docs/skills/{skill-name}-skill.md` |
| How does cron scheduling work? | `docs/scheduling/cron-setup.md` |
| How does Discord delivery work? | `docs/discord/message-delivery.md` |
| What are the report formatting rules? | `docs/output-format/formatting-rules.md` |
| What are the paper trading rules? | `strategy/PAPER.md` |
| What are my experience tagging rules? | `experience/README.md` |

All paths are relative to the workspace root (`{baseDir}/../../`).

## 2. If Docs Don't Answer It — Read Code

Only go to code after checking docs. The codebase lives at:

```
{baseDir}/../../options-toolkit/
  eva.py                    <- CLI entry point
  eva/
    cli.py                  <- Argument parsing, subcommand routing
    commands.py             <- All subcommand implementations (price, chain, report, buy, sell, etc.)
    evaluate.py             <- The evaluate --all pipeline (portfolio fetch, ticker analysis, position detection)
    tradier.py              <- Tradier API calls (market data, orders, account)
    storage.py              <- Data file read/write (snapshots, IV, paper trading local files)
    formatters.py           <- Report output formatting (tables, chunks, Discord-safe output)
    analysis.py             <- IV rank/percentile computation, trend analysis
    news.py                 <- News fetching and deep research (article extraction)
    symbols.py              <- OCC symbol parsing, expiry formatting
```

### Reading Strategy

1. For "what does command X do?" — start at `commands.py`, find the function
2. For "how does the API call work?" — check `tradier.py`
3. For "where is this data saved?" — check `storage.py`
4. For "how is this output formatted?" — check `formatters.py`
5. For "how does evaluate decide what to do?" — that's YOU (the skill), not the code. The code just provides data; your skills define the decision process.

## 3. Workspace Config & Identity

| What | Where |
|------|-------|
| Who you are | `IDENTITY.md`, `SOUL.md` |
| How you behave | `AGENTS.md` |
| Who you're helping | `USER.md` |
| Your memories | `memory/YYYY-MM-DD.md`, `MEMORY.md` |
| Ticker lists | `options-toolkit/tickers.json` (reports), `options-toolkit/trading_tickers.json` (paper trading) |
| Agent config | `~/.openclaw/openclaw.json` |

## 4. Report What You Found

Summarize what you learned. If the docs and code disagree, flag it — docs are authoritative.

## Guardrails

- This is READ-ONLY. Do not modify any files through this skill.
- Docs first, code second. Always.
- If you can't find the answer in docs or code, say so — don't guess.
