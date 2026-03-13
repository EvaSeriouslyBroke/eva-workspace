# TOOLS.md - Options Toolkit Reference

## Toolkit Location

```
~/.openclaw/workspace/options-toolkit/eva.py
```

## Commands

```bash
# Price check
python3 eva.py price --ticker IWM
python3 eva.py price --ticker IWM --json

# Options chain (10 strikes near ATM, ~120 DTE)
python3 eva.py chain --ticker IWM
python3 eva.py chain --ticker IWM --dte 60

# News + sentiment
python3 eva.py news --ticker IWM

# IV history from stored data (no API calls)
python3 eva.py history --ticker IWM
python3 eva.py history --ticker IWM --days 10

# Full report (always use --force for interactive)
python3 eva.py report --ticker IWM --force
```

## Data Location

```
options-toolkit/data/
  {TICKER}/{YYYY}-W{WW}/{YYYY-MM-DD}.json   # Daily snapshots
  cron.log                                     # Cron stderr output
```

## Config

```
options-toolkit/tickers.json    # Tickers + Discord channel for scheduled reports
```

## Cron

Reports run at 6 scheduled times during each trading day (9:31, 11:00, 12:30, 14:00, 15:00, 15:59 ET) plus a 4:01 PM summary, via `run_all.sh`. Crontab fires at both EST and EDT UTC equivalents; eva.py self-filters to the correct ET time.

See `docs/scheduling/cron-setup.md` for the full crontab entries and timezone handling.

## Paper Trading

```
~/.openclaw/workspace/options-toolkit/eva.py
```

### Commands

```bash
# Evaluation JSON (respects market hours, use --force to bypass)
python3 eva.py evaluate --ticker IWM
python3 eva.py evaluate --ticker IWM --force
python3 eva.py evaluate --all            # All tickers from trading_tickers.json

# Portfolio status (formatted for Discord)
python3 eva.py status

# Buy a call or put
python3 eva.py buy --ticker IWM --type call --strike 265 --expiry 2026-06-30 --reason "Mean reversion — dipped 3%"

# Sell to close
python3 eva.py sell --ticker IWM --type call --strike 265 --expiry 2026-06-30 --reason "Thesis played out"

# Order history with reasoning
python3 eva.py trade-history
python3 eva.py trade-history --limit 50

# Reset (user-only, never autonomous)
python3 eva.py reset --confirm
```

All commands accept `--mode paper|real` (default: paper). Real mode is not implemented yet.

### Config

```
~/.openclaw/tradier.json       # Tradier API credentials (outside repo)
```

### Paper Trading Data

```
options-toolkit/data/paper-trading/
  reasons.json            # Order ID → reasoning mapping
  known_positions.json    # Position tracker (entries deleted on close)
  log.jsonl               # Structured event log
  position-snapshots/     # Per-position price/IV/Greeks history
    {OCC_SYMBOL}.jsonl    # One file per position (append-only)

options-toolkit/data/{mode}/{TICKER}/iv/
  {YYYY-MM-DD}.json       # IV snapshots per ticker (built by evaluate)
```

### Paper Trading Cron

Evaluation runs every 15 min during market hours via OpenClaw cron → `paper-trade-evaluate` skill → Discord `paper-trading` channel.

## Key Metrics to Know

| Metric | Bullish Signal | Bearish Signal |
|--------|---------------|----------------|
| P/C Vol Ratio | < 0.8 | > 1.2 |
| P/C OI Ratio | < 0.8 | > 1.2 |
| IV Level | <= 15% (cheap) | > 35% (expensive) |
| IV Trend | Contracting (< -2) | Expanding (> +2) |
| Skew | < -2 (call skew) | > 2 (put skew), > 5 (extreme) |
