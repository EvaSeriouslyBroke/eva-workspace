# Options Toolkit Documentation

This is the complete specification for the Options Toolkit system — a scheduled and interactive options analysis platform built for Eva (OpenClaw agent) and her team.

The toolkit fetches live options data via Tradier API, generates structured analysis reports, stores historical IV data for trend tracking, and delivers results to Discord. It runs on two paths: **scheduled** (system cron at 6 specific times per trading day) and **interactive** (Eva responds to user requests via OpenClaw skills).

---

## Who This Is For

- **Eva** — the AI agent that runs skills and delivers reports
- **Any developer** implementing or modifying the toolkit
- **Any agent** that needs to understand how the system works

---

## How to Read These Docs

1. Start with **[Architecture](architecture/system-design.md)** to understand how everything connects
2. Read **[Design Decisions](architecture/design-decisions.md)** to understand *why* things are built this way
3. Dive into **[Toolkit](toolkit/overview.md)** for the CLI interface and each subcommand
4. Check **[Output Format](output-format/formatting-rules.md)** for exact report formatting rules
5. Read **[Paper Trading](paper-trading/overview.md)** for the autonomous trading system
6. Browse **[Skills](skills/how-skills-work.md)**, **[Scheduling](scheduling/cron-setup.md)**, and **[Discord](discord/message-delivery.md)** as needed

---

## Directory Map

```
docs/
├── README.md                              ← You are here
│
├── architecture/
│   ├── system-design.md                   ← Components, data flow, how everything connects
│   └── design-decisions.md                ← Why Tradier, why system cron, why split skills, etc.
│
├── toolkit/
│   ├── overview.md                        ← eva.py CLI interface, subcommands, common flags
│   ├── price-command.md                   ← `price` subcommand: inputs, logic, output format
│   ├── chain-command.md                   ← `chain` subcommand: inputs, logic, output format
│   ├── news-command.md                    ← `news` subcommand: inputs, logic, output format
│   ├── news-research-command.md           ← `eva.py news-research`: deep article extraction
│   ├── history-command.md                 ← `history` subcommand: inputs, logic, output format
│   ├── snapshots-command.md               ← `snapshots` subcommand: browse/peaks market snapshots
│   ├── report-command.md                  ← `report` subcommand: full report generation
│   └── summary-command.md                 ← `summary` subcommand: end-of-day summary with analysis
│
├── data/
│   ├── storage-format.md                  ← Directory layout, JSON schemas, file naming
│   └── comparison-logic.md                ← How previous runs are found, IV change calculations
│
├── skills/
│   ├── how-skills-work.md                 ← OpenClaw skill system explained
│   ├── stock-price-skill.md               ← Trigger phrases, exec command, expected output
│   ├── options-chain-skill.md             ← Trigger phrases, exec command, expected output
│   ├── stock-news-skill.md                ← Trigger phrases, exec command, expected output
│   ├── stock-news-deep-skill.md           ← Deep news analysis: triggers, AI synthesis rules
│   ├── options-history-skill.md           ← Trigger phrases, exec command, expected output
│   ├── market-snapshots-skill.md          ← Trigger phrases, exec command, expected output
│   ├── options-report-skill.md            ← Trigger phrases, exec command, expected output
│   ├── options-summary-skill.md          ← EOD summary: triggers, analysis output
│   ├── paper-trade-evaluate-skill.md    ← Autonomous trading cycle: context, evaluation, execution
│   ├── paper-trade-reflect-skill.md    ← Experience creation from closed trades
│   ├── paper-trade-hindsight-skill.md  ← Post-sale hindsight analysis
│   ├── paper-trade-strategy-skill.md   ← Strategy modification with no-assumptions enforcement
│   ├── paper-trade-status-skill.md      ← Portfolio status: triggers, output
│   ├── paper-trade-history-skill.md     ← Trade history: triggers, output
│   └── workspace-lookup-skill.md        ← Self-reference: docs-first codebase navigation
│
├── output-format/
│   ├── formatting-rules.md                ← Dividers, emoji, numbers, signs, colors
│   ├── sections-header-price.md            ← Chunk 1: history, header, price
│   ├── sections-options-tables.md         ← Chunk 2: expiry, call table, put table
│   └── sections-iv-summary.md             ← Chunk 3: IV averages, volume, OI, skew + footer
│
├── paper-trading/
│   ├── overview.md                        ← System description, data isolation, settlement
│   ├── commands.md                        ← Every subcommand with flags, examples, API endpoints
│   └── experience-system.md              ← Thesis design, file format, evolution lifecycle
│
├── scheduling/
│   ├── cron-setup.md                      ← Crontab config, timezone, market hours guard
│   └── run-all-script.md                  ← run_all.sh: ticker loop, Discord delivery
│
└── discord/
    └── message-delivery.md                ← Chunk splitting, rate limits, error handling
```

---

## Key References

- **tickers.json** — Ticker list and Discord channel ID for scheduled runs.
- **AGENTS.md** (`~/.openclaw/workspace/AGENTS.md`) — How Eva behaves, memory system, platform rules.
- **IDENTITY.md** (`~/.openclaw/workspace/IDENTITY.md`) — Eva's name, emoji, vibe.

---

## File Locations

```
~/.openclaw/workspace/
  options-toolkit/
    eva.py                  ← CLI entry point
    eva/                    ← Python package (cli, commands, formatters, etc.)
    tickers.json            ← Ticker list + Discord channel (reports)
    trading_tickers.json    ← Ticker list (paper trading evaluate --all)
    run_all.sh              ← Cron wrapper script
    tradier.json            ← Tradier API credentials
    data/                   ← Persistent history (grows forever)
      {TICKER}/
        {YYYY}-W{WW}/
          {YYYY-MM-DD}.json
        snapshots/          ← Market snapshots (primary)
        iv/                 ← IV snapshots (legacy fallback)
      paper-trading/        ← Paper trading local data
        reasons.json
        known_positions.json
        closed_watches.json
        pending_experience_updates.json
        log.jsonl
        position-snapshots/
        post-sale-snapshots/
  strategy/
    PAPER.md                ← Paper trading rules
  experience/
    README.md               ← Experience system docs
    INDEX.md                ← Experience lookup table
    general/                ← Market-wide patterns
    tickers/                ← Per-ticker patterns
  skills/
    stock-price/SKILL.md
    options-chain/SKILL.md
    stock-news/SKILL.md
    stock-news-deep/SKILL.md
    options-history/SKILL.md
    market-snapshots/SKILL.md
    options-report/SKILL.md
    options-summary/SKILL.md
    paper-trade-evaluate/SKILL.md
    paper-trade-reflect/SKILL.md
    paper-trade-hindsight/SKILL.md
    paper-trade-strategy/SKILL.md
    paper-trade-status/SKILL.md
    paper-trade-history/SKILL.md
    workspace-lookup/SKILL.md
  docs/                     ← This documentation
```
