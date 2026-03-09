# Toolkit Overview

`eva.py` is the CLI entry point that powers everything. It delegates to the `eva` package — a set of Python modules that fetch market data via Tradier API, generate formatted reports, store history, and output text.

---

## CLI Synopsis

```
python3 eva.py <command> --ticker <SYM> [flags]
```

### Market Data Subcommands

| Command | Purpose | Typical Use |
|---------|---------|-------------|
| `price` | Current price, previous close, dollar and percent change | Quick price check |
| `chain` | Options chain (10 strikes, calls + puts) | See current options pricing |
| `news` | Headlines + sentiment analysis | Check market news for a ticker |
| `news-research` | Deep article extraction + web search | In-depth news analysis |
| `history` | Recent IV history from stored data | Track IV trends over days |
| `report` | Facts-only options data report | Complete options data snapshot |
| `summary` | End-of-day summary with analysis | After-close recap of the day's moves |

### Paper Trading Subcommands

| Command | Purpose | Typical Use |
|---------|---------|-------------|
| `evaluate` | Build evaluation JSON for trading decisions | Autonomous trading cycle |
| `status` | Portfolio status (balances, positions, orders) | Check current state |
| `buy` | Place a buy_to_open order | Open a new position |
| `sell` | Place a sell_to_close order | Close an existing position |
| `hindsight` | Post-sale hindsight analysis | Review sell timing vs actual outcomes |
| `pending-experience` | Show/clear pending experience updates | Inspect reflect queue |
| `trade-history` | Order history with reasoning | Review past trades |
| `reset` | Cancel all orders, close positions | Clean slate (user-only) |

### Common Flags

| Flag | Applies To | Required | Description |
|------|-----------|----------|-------------|
| `--ticker <SYM>` | price, chain, news, news-research, history, report, summary, buy, sell | Yes | Ticker symbol (e.g., IWM, SPY, QQQ) |
| `--ticker <SYM>` or `--all` | evaluate | One required | Single ticker or all from trading_tickers.json |
| `--mode paper\|real` | All commands | No | Trading mode (default: paper) |
| `--force` | report, summary, evaluate | No | Skip schedule/market hours check |
| `--json` | price, chain, news, history, report | No | Output raw JSON instead of formatted text |
| `--dte <N>` | chain | No | Target DTE for expiry selection (default: 120) |
| `--days <N>` | history | No | Number of trading days to show (default: 5) |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success — output was produced, or silent exit (outside scheduled time / market closed) |
| 1 | Error — something went wrong (invalid ticker, network failure, etc.) |

**Silent exit** (code 0, no output): This happens when `report` or `summary` is called without `--force` and the current time doesn't match the command's schedule. The script exits cleanly with no stdout. This tells the caller "nothing to do" — `run_all.sh` skips sending to Discord, Eva doesn't reply.

---

## Output Streams

| Stream | Contains | When |
|--------|----------|------|
| stdout | Formatted report text or JSON data | Successful execution with data |
| stderr | Error messages, warnings | Something went wrong |
| (nothing) | No output at all | Outside scheduled time (without `--force`) |

**This separation is critical**: `run_all.sh` captures stdout and sends it to Discord. If errors went to stdout, users would receive error messages in Discord. By keeping errors on stderr, they go to the cron log instead.

---

## Market Hours / Schedule Check

The `report` and `summary` commands include schedule guards:

```
report: runs at SCHEDULE times [(9,31), (11,0), (12,30), (14,0), (15,0), (15,59)]
summary: runs at SUMMARY_SCHEDULE times [(16,1)]

Both check:
  - Day: Monday through Friday only
  - Time: must match the command's schedule
  - If not matching and --force not set: exit 0, no output
  - If --force is set: skip this check entirely
```

The `evaluate` command checks if the market is open via Tradier's `/markets/clock` endpoint. If closed, it exits silently unless `--force` is passed.

These checks use Python's `zoneinfo` module with `America/New_York`, which handles DST correctly. The check is performed before any API calls.

Other subcommands (`price`, `chain`, `news`, `news-research`, `history`) do NOT have schedule checks. They always return data when asked.

---

## Package Structure

The code is organized as a Python package:

```
options-toolkit/
  eva.py                  ← Entry point (imports from eva.cli)
  eva/
    __init__.py            ← Constants (ET timezone, dividers, paths, Discord channel)
    cli.py                 ← argparse setup and dispatch
    commands.py            ← All cmd_* handler functions
    formatters.py          ← All format_* functions, schedule guards
    analysis.py            ← Sentiment scoring, directional scoring, trends, chain summary, IV rank
    storage.py             ← File persistence (snapshots, reasons, positions, log, IV history)
    news.py                ← DuckDuckGo news fetching, article extraction, deep research
    tradier.py             ← Tradier API client (config, HTTP helpers, all data fetchers)
    symbols.py             ← OCC symbol building/parsing, expiry/strike selection
    evaluate.py            ← Paper trading evaluation builder, closed position detection
```

### Key Functions by Module

**Tradier API (tradier.py)**:
- `load_config(mode)` — Load Tradier credentials for paper/real mode
- `fetch_price(cfg, sym)` — Returns price dict via Tradier quotes
- `fetch_options_chain(cfg, sym, target_dte)` — Returns structured chain with calls, puts, price data
- `fetch_quote(cfg, sym)` — Raw Tradier quote
- `fetch_chain_raw(cfg, sym, expiry)` — Raw option chain with greeks
- `fetch_expirations(cfg, sym)` — Available expiration dates
- `fetch_history(cfg, sym, days)` — Daily price history
- `fetch_balances(cfg)`, `fetch_positions(cfg)`, `fetch_orders(cfg)` — Account data
- `is_market_open(cfg)` — Check market state via `/markets/clock`

**News (news.py)**:
- `fetch_news(cfg, sym)` — Headlines + sentiment from DuckDuckGo
- `fetch_headlines(ticker)` — Raw DuckDuckGo news search
- `research(ticker, ...)` — Deep news research with article extraction

**Formatters (formatters.py)**:
- `format_price(data)` — Price output
- `format_chain(data, prev)` — Options chain cards
- `format_news(data)` — News headlines + sentiment
- `format_history_iv(snapshots, sym)` — IV history table
- `format_iv_summary(data, prev)` — IV metrics summary
- `format_report(cfg, sym, force)` — Full report (fetches + formats + saves)
- `format_summary(sym, force)` — End-of-day summary
- `format_status(balances, positions, orders)` — Portfolio status
- `format_trade_history(orders, reasons, limit)` — Trade history with reasoning

**Storage (storage.py)**:
- `save_snapshot(sym, data)` — Append snapshot to daily JSON file
- `load_previous(sym)` — Most recent snapshot from history
- `load_history(sym, days)` — Recent snapshots for history view
- `load_today_snapshots(sym)` — All snapshots from today for EOD summary
- `load_reasons(mode)`, `save_reasons(mode, reasons)` — Trade reasoning
- `load_known_positions(mode)`, `save_known_positions(mode, positions)` — Position tracking
- `save_position_snapshot(mode, symbol, snapshot)` — Append price/IV/Greeks snapshot for a position
- `load_position_snapshots(mode, symbol)` — Load all snapshots for a position
- `count_position_snapshots(mode, symbol)` — Count snapshots without parsing
- `load_closed_watches(mode)`, `save_closed_watches(mode, watches)` — Closed watch tracking
- `save_post_sale_snapshot(mode, symbol, snapshot)` — Append post-sale price/IV/Greeks snapshot
- `load_post_sale_snapshots(mode, symbol)` — Load all post-sale snapshots for a closed watch

**Analysis (analysis.py)**:
- `score_sentiment(articles)` — Keyword-based news sentiment
- `compute_directional_score(data)` — Bullish/bearish scoring
- `compute_trends(history, price)` — SMA, returns, trend summary
- `build_chain_summary(chain, price)` — Near-money options summary
- `compute_iv_rank(current_iv, history)` — IV rank and percentile

**Symbols (symbols.py)**:
- `build_occ_symbol(ticker, expiry, type, strike)` — Build OCC option symbol
- `parse_occ_symbol(sym)` — Parse OCC symbol into components
- `extract_greeks(opt)` — Extract IV (%) and rounded Greeks dict from a raw chain option
- `select_expiry(expirations, target_dte)` — Pick closest expiry to target DTE
- `select_strikes(strikes, price, count)` — Pick nearest strikes to price

### CLI Entry Point
- `eva.py` imports `main()` from `eva.cli`
- Uses `argparse` with subcommands
- Each subcommand maps to a `cmd_*` handler in `eva.commands`
- Handler calls API fetchers → formatters → (optionally) storage → prints to stdout

---

## Ticker Handling

- Ticker symbols are passed as `--ticker <SYM>` and uppercased internally
- Any valid Tradier-supported ticker works (stocks, ETFs)
- The report header dynamically uses the ticker name (not hardcoded to "IWM")
- Invalid tickers cause the Tradier API to return errors, caught and sent to stderr

---

## JSON Mode

When `--json` is passed, instead of formatted text, the command outputs a JSON object with all computed values. This enables:
- Programmatic consumption by other tools
- Testing (easier to assert on structured data than formatted text)
- Future integrations

Available on: `price`, `chain`, `news`, `history`, `report`. Not available on: `summary`, `evaluate`, `status`, `buy`, `sell`, `trade-history`, `reset`.

Each command's JSON schema is documented in its respective doc file.
