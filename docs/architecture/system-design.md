# System Design

This document describes every component of the Options Toolkit, how they connect, and how data flows through the system.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SCHEDULED PATH                               │
│                                                                     │
│  System Cron (*/30 min, Mon-Fri 9-16 ET)                           │
│       │                                                             │
│       ▼                                                             │
│  run_all.sh                                                         │
│       │  reads tickers.json                                         │
│       │  for each ticker:                                           │
│       ▼                                                             │
│  python3 toolkit.py report --ticker <SYM>                          │
│       │  checks market hours (9:30-16:00 ET)                       │
│       │  if outside hours → silent exit (no output)                │
│       │  if inside hours:                                          │
│       ▼                                                             │
│  ┌──────────────────────┐                                          │
│  │  yfinance API calls  │                                          │
│  │  • price data        │                                          │
│  │  • options chain     │                                          │
│  │  • news headlines    │                                          │
│  └──────────┬───────────┘                                          │
│             │                                                       │
│             ▼                                                       │
│  ┌──────────────────────┐     ┌─────────────────────┐              │
│  │  Load previous run   │────▶│  data/{TICKER}/     │              │
│  │  from history        │◀────│  {week}/{date}.json │              │
│  └──────────┬───────────┘     └─────────────────────┘              │
│             │                                                       │
│             ▼                                                       │
│  ┌──────────────────────┐                                          │
│  │  Generate report     │                                          │
│  │  (8 sections)        │                                          │
│  │  with ---SPLIT---    │                                          │
│  │  markers             │                                          │
│  └──────────┬───────────┘                                          │
│             │                                                       │
│             ▼                                                       │
│  ┌──────────────────────┐                                          │
│  │  Save snapshot to    │                                          │
│  │  data/{TICKER}/...   │                                          │
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
│  exec: python3 toolkit.py report --ticker IWM --force              │
│       │  --force bypasses market hours check                       │
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

### 1. `toolkit.py` — Main CLI Entry Point

- **Location**: `~/.openclaw/workspace/options-toolkit/toolkit.py`
- **Language**: Python 3.x
- **Size**: ~550 lines (single file)
- **Interface**: CLI with subcommands (`price`, `chain`, `news`, `history`, `report`, `summary`)
- **Dependencies**: `yfinance`, standard library (`json`, `datetime`, `argparse`, `sys`, `os`, `math`)
- **Behavior**: Pure stdout-based — output goes to stdout, errors go to stderr
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
- **Size**: ~30 lines
- **Purpose**: Loop through tickers, run reports, split output, send to Discord
- **Called by**: System crontab

### 4. `data/` — Persistent History Store

- **Location**: `~/.openclaw/workspace/options-toolkit/data/`
- **Structure**: `{TICKER}/{YYYY}-W{WW}/{YYYY-MM-DD}.json`
- **Growth**: ~20MB/year per ticker (never deleted)
- **Purpose**: Enable IV trend analysis across runs

### 5. `news_research.py` — Deep News Research

- **Location**: `~/.openclaw/workspace/options-toolkit/news_research.py`
- **Language**: Python 3.x
- **Size**: ~250 lines (single file)
- **Interface**: CLI with `--ticker`, `--max-articles`, `--max-search` flags
- **Dependencies**: `trafilatura`, `duckduckgo-search`, `yfinance`, standard library
- **Behavior**: Pure stdout-based JSON output, errors to stderr
- **Purpose**: Fetches full article content from yfinance URLs via trafilatura, searches DuckDuckGo for additional context, outputs structured JSON for Eva to synthesize
- **Relationship to toolkit.py**: Separate standalone script. Shares sentiment algorithm (duplicated, not imported). Does not affect cron or existing toolkit commands.

### 6. SKILL.md Files (7 total)

- **Location**: `~/.openclaw/workspace/skills/{skill-name}/SKILL.md`
- **Purpose**: Tell Eva when and how to run toolkit commands
- **Skills**: stock-price, options-chain, stock-news, stock-news-deep, options-history, options-report, options-summary

### 7. `cron.log` — Execution Log

- **Location**: `~/.openclaw/workspace/options-toolkit/data/cron.log`
- **Contents**: stderr output from cron runs (errors, warnings)
- **Rotation**: Not yet implemented

---

## Dependencies

| Dependency | Version | Purpose | Used by |
|------------|---------|---------|---------|
| Python 3 | 3.13+ | Runtime | All scripts |
| yfinance | latest | Market data (price, options, news) | toolkit.py, news_research.py |
| trafilatura | latest | Full article content extraction from URLs | news_research.py only |
| duckduckgo-search | latest | Web search without API keys | news_research.py only |
| cron (system) | any | Scheduled execution | run_all.sh |
| openclaw CLI | 2026.2+ | Discord message delivery, skill system | run_all.sh, skills |
| bash | any | run_all.sh execution | run_all.sh |

### Python Standard Library Modules Used

- `argparse` — CLI argument parsing
- `json` — Data serialization
- `datetime`, `zoneinfo` — Time handling, market hours check
- `sys` — stdout/stderr separation
- `os` — File path operations, mkdir
- `math` — Rounding for ATM strike

---

## Data Flow Details

### Scheduled Run (Every 10 Minutes)

1. Cron fires `run_all.sh`
2. Script reads `tickers.json` for ticker list and Discord channel
3. For each ticker:
   a. Runs `python3 toolkit.py report --ticker <SYM>`
   b. toolkit.py checks if current time is 9:30-16:00 ET
   c. If outside hours: exits with code 0, no output → script skips
   d. If inside hours: fetches data, generates report, saves snapshot
   e. Output goes to stdout with `---SPLIT---` markers between chunks
4. Script splits output using awk on `---SPLIT---`
5. Each chunk sent via `openclaw message send`
6. 1s sleep between chunks, 2s sleep between tickers

### Interactive Request

1. User asks Eva something matching a skill trigger
2. Eva's skill description (always in context) matches the intent
3. Eva loads the skill body and follows its instructions
4. Eva runs `exec: python3 toolkit.py <command> --ticker <SYM> [--force]`
5. For `report`: `--force` is always passed (skip market hours check)
6. Eva captures stdout
7. For multi-chunk output: Eva splits at `---SPLIT---` and sends each part
8. For single-chunk commands (`price`, `chain`, `news`, `history`): Eva posts directly

### Data Storage Flow

1. After generating a report, toolkit.py creates a snapshot JSON object
2. Determines the week folder: `data/{TICKER}/{YYYY}-W{WW}/`
3. Creates directory with `mkdir -p` if needed
4. Loads existing daily file (`{YYYY-MM-DD}.json`) or creates empty array
5. Appends new snapshot to array
6. Writes array back to file
7. Prints "Saved IV data for next comparison"

---

## File Paths Summary

```
~/.openclaw/
  workspace/
    OUTPUT.md                              ← Authoritative output format spec
    AGENTS.md                              ← Agent behavior rules
    IDENTITY.md                            ← Eva identity
    SOUL.md                                ← Agent philosophy

    options-toolkit/
      toolkit.py                           ← Main CLI
      news_research.py                     ← Deep news research (standalone)
      tickers.json                         ← Ticker config
      run_all.sh                           ← Cron wrapper
      data/
        cron.log                           ← Execution log
        IWM/
          2026-W08/
            2026-02-17.json
            2026-02-18.json
          2026-W09/
            2026-02-20.json

    skills/
      stock-price/SKILL.md
      options-chain/SKILL.md
      stock-news/SKILL.md
      stock-news-deep/SKILL.md
      options-history/SKILL.md
      options-report/SKILL.md
      options-summary/SKILL.md

    docs/                                  ← This documentation
```
