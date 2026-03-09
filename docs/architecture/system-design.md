# System Design

This document describes every component of the Options Toolkit, how they connect, and how data flows through the system.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SCHEDULED PATH                               │
│                                                                     │
│  System Cron (6 scheduled times, Mon-Fri, ET)                      │
│       │                                                             │
│       ▼                                                             │
│  run_all.sh                                                         │
│       │  reads tickers.json                                         │
│       │  for each ticker:                                           │
│       ▼                                                             │
│  python3 eva.py report --ticker <SYM>                              │
│       │  checks if current ET time matches SCHEDULE                │
│       │  if not scheduled → silent exit (no output)                │
│       │  if scheduled:                                             │
│       ▼                                                             │
│  ┌──────────────────────┐                                          │
│  │  Tradier API calls   │                                          │
│  │  • price data        │                                          │
│  │  • options chain     │                                          │
│  └──────────┬───────────┘                                          │
│             │                                                       │
│             ▼                                                       │
│  ┌──────────────────────┐     ┌─────────────────────┐              │
│  │  Load previous run   │────▶│  data/{mode}/{TICKER}/│              │
│  │  from history        │◀────│  {week}/{date}.json │              │
│  └──────────┬───────────┘     └─────────────────────┘              │
│             │                                                       │
│             ▼                                                       │
│  ┌──────────────────────┐                                          │
│  │  Generate report     │                                          │
│  │  (3 chunks)          │                                          │
│  │  with ---SPLIT---    │                                          │
│  │  markers             │                                          │
│  └──────────┬───────────┘                                          │
│             │                                                       │
│             ▼                                                       │
│  ┌──────────────────────┐                                          │
│  │  Save snapshot to    │                                          │
│  │  data/{mode}/{TICKER}/│                                          │
│  └──────────┬───────────┘                                          │
│             │                                                       │
│             ▼  stdout                                               │
│  run_all.sh splits at ---SPLIT---                                   │
│       │                                                             │
│       ▼                                                             │
│  openclaw message send --channel discord --target <CHANNEL>         │
│       │  (one message per chunk, 1s sleep between)                 │
│       ▼                                                             │
│  ┌──────────┐                                                      │
│  │ Discord  │                                                      │
│  └──────────┘                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       INTERACTIVE PATH                              │
│                                                                     │
│  User in Discord: "what's the play on IWM?"                        │
│       │                                                             │
│       ▼                                                             │
│  Eva (OpenClaw agent)                                               │
│       │  skill description matches → loads skill body              │
│       ▼                                                             │
│  exec: python3 eva.py report --ticker IWM --force                  │
│       │  --force bypasses schedule check                           │
│       ▼                                                             │
│  (same pipeline as above: fetch → compare → generate → save)       │
│       │                                                             │
│       ▼  stdout captured by Eva                                    │
│  Eva splits at ---SPLIT--- markers                                  │
│  Eva sends each chunk as a Discord message                          │
│       │                                                             │
│       ▼                                                             │
│  ┌──────────┐                                                      │
│  │ Discord  │                                                      │
│  └──────────┘                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Inventory

### 1. `eva.py` + `eva/` package — Main CLI

- **Location**: `~/.openclaw/workspace/options-toolkit/eva.py` (entry point) + `eva/` package
- **Language**: Python 3.x
- **Interface**: CLI with subcommands (`price`, `chain`, `news`, `news-research`, `history`, `report`, `summary`, `evaluate`, `status`, `buy`, `sell`, `trade-history`, `pending-experience`, `reset`)
- **Dependencies**: `requests`, `duckduckgo-search`, `trafilatura`, standard library (`json`, `datetime`, `argparse`, `sys`, `os`, `statistics`, `zoneinfo`)
- **Behavior**: Stdout-based — output goes to stdout, errors go to stderr. Exception: `buy` and `sell` commands also send Discord trade notifications via `openclaw message send`.
- **Exit codes**: 0 = success (with or without output), 1 = error

### 2. `tickers.json` — Configuration

- **Location**: `~/.openclaw/workspace/options-toolkit/tickers.json`
- **Contents**: List of ticker symbols and Discord channel ID
- **Format**:
  ```json
  {
    "tickers": ["IWM"],
    "discord_channel": "1474439221140787392"
  }
  ```

### 3. `run_all.sh` — Cron Wrapper

- **Location**: `~/.openclaw/workspace/options-toolkit/run_all.sh`
- **Purpose**: Loop through tickers, run reports + summaries, split output, send to Discord
- **Called by**: System crontab

### 4. `data/` — Persistent History Store

- **Location**: `~/.openclaw/workspace/options-toolkit/data/`
- **Structure**: `{mode}/{TICKER}/{YYYY}-W{WW}/{YYYY-MM-DD}.json`
- **Mode separation**: Market data (snapshots, IV, news) stored under `data/{mode}/{TICKER}/` because Tradier sandbox (paper) data is 15-min delayed vs real-time (live). Storage functions take a `mode` parameter.
- **Growth**: ~3MB/year per ticker (never deleted)
- **Purpose**: Enable IV trend analysis across runs

### 5. `eva.py news-research` — Deep News Research

- **Subcommand of**: `eva.py`
- **Interface**: `eva.py news-research --ticker <SYM> [--max-articles 3] [--max-search 5]`
- **Dependencies**: `trafilatura`, `duckduckgo-search`
- **Behavior**: Pure stdout-based JSON output, errors to stderr
- **Purpose**: Fetches news via DuckDuckGo, extracts full article content via trafilatura, outputs structured JSON for Eva to synthesize

### 6. SKILL.md Files (11 total)

- **Location**: `~/.openclaw/workspace/skills/{skill-name}/SKILL.md`
- **Purpose**: Tell Eva when and how to run toolkit commands
- **Skills**: stock-price, options-chain, stock-news, stock-news-deep, options-history, options-report, options-summary, paper-trade-evaluate, paper-trade-reflect, paper-trade-status, paper-trade-history

### 7. Paper Trading Subcommands (in `eva.py`)

- **Subcommands**: `evaluate`, `status`, `buy`, `sell`, `trade-history`, `reset`
- **Dependencies**: `requests`, standard library
- **Behavior**: Stdout-based — output goes to stdout, errors go to stderr. `buy` and `sell` also send trade notification messages to the paper-trading Discord channel.
- **Exit codes**: 0 = success, 1 = error
- **Config**: Reads `tradier.json` for API credentials per mode
- **Local data**: `data/{mode}-trading/` — reasons, known positions, position snapshots, event log

### 8. `tradier.json` — Tradier API Config

- **Location**: `~/.openclaw/workspace/options-toolkit/tradier.json`
- **Contents**: API token, account ID, and base URL per mode (paper/real)
- **Not version controlled** — contains secrets

### 9. Experience System

- **Location**: `~/.openclaw/workspace/experience/`
- **Purpose**: Living knowledge base of trading theses, refined by evidence
- **Written by**: Eva (LLM), not code — requires judgment for categorization
- **Key files**: `INDEX.md` (lookup table), `general/` and `tickers/` (thesis files)

### 10. Strategy

- **Location**: `~/.openclaw/workspace/strategy/PAPER.md`
- **Purpose**: Trading rules Eva reads before every evaluation cycle
- **Living document**: Eva can make small evidence-backed refinements

### 11. `cron.log` — Execution Log

- **Location**: `~/.openclaw/workspace/options-toolkit/data/cron.log`
- **Contents**: stderr output from cron runs (errors, warnings)
- **Rotation**: Not yet implemented

---

## Dependencies

| Dependency | Version | Purpose | Used by |
|------------|---------|---------|---------|
| Python 3 | 3.13+ | Runtime | All scripts |
| requests | latest | HTTP client for Tradier API | eva.py (all market data + trading) |
| duckduckgo-search | latest | News headline fetching | eva.py news + news-research |
| trafilatura | latest | Full article content extraction from URLs | eva.py news-research only |
| cron (system) | any | Scheduled execution | run_all.sh |
| openclaw CLI | 2026.2+ | Discord message delivery, skill system | run_all.sh, skills |
| bash | any | run_all.sh execution | run_all.sh |

### Python Standard Library Modules Used

- `argparse` — CLI argument parsing
- `json` — Data serialization
- `datetime`, `zoneinfo` — Time handling, schedule checks
- `sys` — stdout/stderr separation
- `os` — File path operations, mkdir
- `statistics` — Mean computation for IV averages
- `concurrent.futures` — Threaded article extraction (news-research)

---

## Data Flow Details

### Scheduled Run (6 Times Per Trading Day)

1. Cron fires `run_all.sh`
2. Script reads `tickers.json` for ticker list and Discord channel
3. For each ticker:
   a. Runs `python3 eva.py report --ticker <SYM>`
   b. eva.py checks if current ET time matches the SCHEDULE (9:31, 11:00, 12:30, 14:00, 15:00, 15:59)
   c. If not scheduled: exits with code 0, no output → script skips
   d. If scheduled: fetches data from Tradier, generates report, saves snapshot
   e. Output goes to stdout with `---SPLIT---` markers between chunks
   f. Runs `python3 eva.py summary --ticker <SYM>`
   g. Summary only produces output at 4:01 PM ET
4. Script splits output using awk on `---SPLIT---`
5. Each chunk sent via `openclaw message send`
6. 1s sleep between chunks, 2s sleep between tickers

### Interactive Request

1. User asks Eva something matching a skill trigger
2. Eva's skill description (always in context) matches the intent
3. Eva loads the skill body and follows its instructions
4. Eva runs `exec: python3 eva.py <command> --ticker <SYM> [--force]`
5. For `report`: `--force` is always passed (skip schedule check)
6. Eva captures stdout
7. For multi-chunk output: Eva splits at `---SPLIT---` and sends each part
8. For single-chunk commands (`price`, `chain`, `news`, `history`): Eva posts directly

### Data Storage Flow

1. After generating a report, eva.py creates a snapshot JSON object
2. Determines the week folder: `data/{mode}/{TICKER}/{YYYY}-W{WW}/`
3. Creates directory with `mkdir -p` if needed
4. Loads existing daily file (`{YYYY-MM-DD}.json`) or creates empty array
5. Appends new snapshot to array
6. Writes array back to file
7. Prints "Saved IV data for next comparison"

### Paper Trading — Autonomous Evaluation (Every 15 Minutes)

1. OpenClaw cron fires `paper-trade-evaluate` skill
2. Eva reads `strategy/PAPER.md` (strategy rules only — no experiences yet)
3. Runs `python3 eva.py evaluate --all`
   a. Checks market state via Tradier `/markets/clock` (skips weekends, holidays, half days)
   b. Fetches account, positions, orders once for all tickers
   c. Per ticker: fetches quote, price history, expirations, chain; uses cached news headlines (fetched once per day, not every cycle)
   d. Builds evaluation JSON with intraday context, recent daily candles, trends, IV context, affordable options (with all Greeks: delta, gamma, theta, vega, rho, open_interest), available expirations (with DTE), and news (today's headlines + 14-day sentiment history)
   e. Records position snapshots (price/IV/Greeks) for open positions belonging to the ticker
   f. Diffs `known_positions.json` against Tradier to detect closed trades; deletes closed entries from `known_positions.json`
   g. Saves IV snapshot for historical tracking; saves news snapshot only if no snapshot exists for today
   h. Outputs JSON array to stdout
4. Recently closed positions are persisted to `pending_experience_updates.json` for the reflect skill
5. Eva makes tentative buy/sell/hold decisions based on strategy + market data
5b. For tickers where Eva plans to buy or double down: runs `news-research` for deep article extraction
6. Eva spawns recall agents to search `experience/` for similar past situations (by ticker + pattern tags)
7. Eva reviews recall findings — confirms, adjusts, or reverses tentative decisions
8. If acting: runs `buy` or `sell` command, posts to Discord paper-trading channel
9. If holding: stays silent

### Paper Trading — Autonomous Reflection (~7 Min After Evaluate)

1. OpenClaw cron fires `paper-trade-reflect` skill
2. Eva reads experience system docs and strategy
3. Runs `python3 eva.py pending-experience` to fetch pending closed positions
4. If pending updates exist: for each closed position, analyzes trade outcome using position snapshots, entry/close reasons, and market context
5. Creates or updates experience files with evidence entries
6. Runs `python3 eva.py pending-experience --clear` to clear the pending file
7. Posts a brief note about what was learned (silent if nothing pending)

### Paper Trading — Interactive (User Request)

1. User asks "paper trading status" or "trade history"
2. Eva's skill matches, runs `eva.py status` or `trade-history`
3. Pre-formatted output posted to Discord as-is

---

## File Paths Summary

```
~/.openclaw/
  workspace/
    AGENTS.md                              ← Agent behavior rules
    IDENTITY.md                            ← Eva identity
    SOUL.md                                ← Agent philosophy

    options-toolkit/
      eva.py                               ← CLI entry point
      eva/                                 ← Python package (cli, commands, formatters, etc.)
      tickers.json                         ← Ticker config (reports)
      trading_tickers.json                 ← Ticker config (paper trading evaluate --all)
      run_all.sh                           ← Cron wrapper
      tradier.json                         ← Tradier API credentials
      data/
        cron.log                           ← Execution log
        paper/                             ← Paper mode market data (15-min delayed)
          IWM/
            2026-W08/
              2026-02-17.json
              2026-02-18.json
            2026-W09/
              2026-02-20.json
            iv/                            ← IV snapshots for rank computation
              2026-03-07.json
            news/                          ← News snapshots for sentiment history
              2026-03-07.json
        live/                              ← Live mode market data (real-time)
        paper-trading/                     ← Paper trading local data
          reasons.json
          known_positions.json
          log.jsonl
          position-snapshots/              ← Per-position price/IV/Greeks history
            {OCC_SYMBOL}.jsonl

    skills/
      stock-price/SKILL.md
      options-chain/SKILL.md
      stock-news/SKILL.md
      stock-news-deep/SKILL.md
      options-history/SKILL.md
      options-report/SKILL.md
      options-summary/SKILL.md
      paper-trade-evaluate/SKILL.md
      paper-trade-reflect/SKILL.md
      paper-trade-status/SKILL.md
      paper-trade-history/SKILL.md

    strategy/
      PAPER.md                             ← Paper trading rules

    experience/
      README.md                            ← Experience system docs
      INDEX.md                             ← Experience lookup table
      general/                             ← Market-wide patterns
      tickers/                             ← Per-ticker patterns

    docs/                                  ← This documentation
```
