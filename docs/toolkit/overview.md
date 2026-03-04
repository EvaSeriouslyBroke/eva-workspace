# Toolkit Overview

`toolkit.py` is the single-file CLI that powers everything. It fetches market data, generates formatted reports, stores history, and outputs text.

---

## CLI Synopsis

```
python3 toolkit.py <command> --ticker <SYM> [flags]
```

### Subcommands

| Command | Purpose | Typical Use |
|---------|---------|-------------|
| `price` | Current price, previous close, dollar and percent change | Quick price check |
| `chain` | Options chain table (5 strikes, calls + puts) | See current options pricing |
| `news` | Headlines + sentiment analysis | Check market news for a ticker |
| `history` | Recent IV history from stored data | Track IV trends over days |
| `report` | Facts-only options data report | Complete options data snapshot |
| `summary` | End-of-day summary with analysis | After-close recap of the day's moves |

### Common Flags

| Flag | Applies To | Required | Description |
|------|-----------|----------|-------------|
| `--ticker <SYM>` | All commands | Yes | Ticker symbol (e.g., IWM, SPY, QQQ) |
| `--force` | `report`, `summary` | No | Skip schedule check |
| `--json` | All commands | No | Output raw JSON instead of formatted text |
| `--dte <N>` | `chain` | No | Target DTE for expiry selection (default: 120) |
| `--days <N>` | `history` | No | Number of trading days to show (default: 5) |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success — output was produced, or silent exit (outside market hours) |
| 1 | Error — something went wrong (invalid ticker, network failure, etc.) |

**Silent exit** (code 0, no output): This happens when `report` or `summary` is called without `--force` and the current time doesn't match the command's schedule. The script exits cleanly with no stdout. This tells the caller "nothing to do" — `run_all.sh` skips sending to Discord, Eva doesn't reply.

---

## Output Streams

| Stream | Contains | When |
|--------|----------|------|
| stdout | Formatted report text or JSON data | Successful execution with data |
| stderr | Error messages, warnings | Something went wrong |
| (nothing) | No output at all | Outside market hours (without `--force`) |

**This separation is critical**: `run_all.sh` captures stdout and sends it to Discord. If errors went to stdout, users would receive error messages in Discord. By keeping errors on stderr, they go to the cron log instead.

---

## Market Hours Check

The `report` and `summary` commands include schedule guards:

```
report: runs at SCHEDULE times [(9,35), (11,0), (12,30), (14,0), (15,0), (15,59)]
summary: runs at SUMMARY_SCHEDULE times [(16,1)]

Both check:
  - Day: Monday through Friday only
  - Time: must match the command's schedule
  - If not matching and --force not set: exit 0, no output
  - If --force is set: skip this check entirely
```

These checks use Python's `zoneinfo` module with `America/New_York`, which handles DST correctly. The check is performed before any API calls.

Other subcommands (`price`, `chain`, `news`, `history`) do NOT have schedule checks. They always return data when asked.

---

## Internal Code Organization

The script is a single file but internally organized into functional groups:

### Fetcher Functions
- `fetch_price(ticker)` — Returns price dict from yfinance
- `fetch_chain(ticker, target_dte)` — Returns options chain data
- `fetch_news(ticker)` — Returns headlines list
- `load_previous(ticker)` — Loads most recent snapshot from history

### Formatter Functions
- `format_price(data)` — Formats Section 3 output
- `format_chain(data)` — Formats Sections 5-7 output
- `format_news(data)` — Formats Section 4 output
- `format_history(snapshots)` — Formats history table
- `format_report(all_data)` — Formats complete report (8 sections + footer) with `---SPLIT---` markers
- `format_summary(sym, force)` — Formats end-of-day summary (3 chunks) with `---SPLIT---` markers

### Storage Functions
- `save_snapshot(ticker, data)` — Appends snapshot to daily JSON file
- `load_history(ticker, days)` — Loads recent snapshots for history view
- `load_today_snapshots(ticker)` — Loads all snapshots from today for EOD summary

### Utility Functions
- `is_scheduled_time()` — Returns bool; checks if current ET time matches a report schedule time
- `is_summary_time()` — Returns bool; checks if current ET time matches the summary schedule (4:01 PM)
- `select_expiry(expirations, target_dte)` — Picks closest expiry to target DTE
- `select_strikes(chain, current_price, count)` — Picks `count` strikes closest to current price (default 5)
- `score_sentiment(headlines)` — Scores news sentiment
- `compute_directional_score(data)` — Computes bullish/bearish scores (used by JSON output mode)

### CLI Entry Point
- Uses `argparse` with subcommands
- Each subcommand maps to a handler function
- Handler calls fetchers → formatters → (optionally) storage → prints to stdout

---

## Ticker Handling

- Ticker symbols are passed as `--ticker <SYM>` and uppercased internally
- Any valid Yahoo Finance ticker works (stocks, ETFs, indices)
- The report header dynamically uses the ticker name (not hardcoded to "IWM")
- Invalid tickers cause yfinance to raise exceptions, caught and sent to stderr

---

## JSON Mode

When `--json` is passed, instead of formatted text, the command outputs a JSON object with all computed values. This enables:
- Programmatic consumption by other tools
- Testing (easier to assert on structured data than formatted text)
- Future integrations

Each command's JSON schema is documented in its respective doc file.
