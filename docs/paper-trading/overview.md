# Paper Trading System — Overview

Eva trades options autonomously in Tradier's sandbox environment, building an experience knowledge base from every trade.

## Architecture

- **API**: Tradier sandbox (`https://sandbox.tradier.com/v1`) — handles portfolio, orders, market data
- **CLI**: `eva.py` — unified CLI with subcommands for evaluate, status, buy, sell, trade-history, reset
- **Strategy**: `strategy/PAPER.md` — unrestricted experimentation (any DTE, any strategy, no position limits)
- **Experiences**: `experience/` — living theses refined by trade evidence and observational patterns
- **Skills**: 3 OpenClaw skills (evaluate, status, history) — 1 autonomous, 2 interactive
- **Cron**: Every 15 minutes during market hours via OpenClaw cron

## Data Isolation

Paper and real trading are fully isolated:
- **Config**: `tradier.json` has separate `paper` and `real` sections (only paper implemented)
- **API**: Sandbox URL vs live URL — never mixed
- **Trading data**: `data/paper-trading/` vs `data/real-trading/` — separate directories for reasons, positions, logs
- **Market data**: `data/paper/{TICKER}/` vs `data/live/{TICKER}/` — separate directories for snapshots, IV, and news (sandbox data is 15-min delayed vs real-time)
- **Discord**: Separate channels per mode

## Local Data (What Tradier Doesn't Store)

Tradier handles portfolio state, orders, and market data. We store only:
- `reasons.json` — maps Tradier order IDs to Eva's reasoning + rich market_context at trade time
- `known_positions.json` — tracks open positions with entry context and market_context (all Greeks, IV rank/percentile, price trends, news); each OCC symbol maps to a list of buy entries (supports averaging into positions); entries deleted when closing is detected
- `log.jsonl` — append-only event log for debugging
- `position-snapshots/{OCC}.jsonl` — per-position price/IV/Greeks history recorded every evaluate cycle

## Closed Position Lifecycle

1. `buy` command appends an entry to the OCC symbol's list in `known_positions.json` with `reflected: false` and rich market_context (multiple buys of the same contract accumulate as separate entries)
2. Each `evaluate` cycle checks Tradier positions — when the position appears, sets `reflected: true` on all unreflected entries
3. Once all entries are reflected, if the position disappears from Tradier → detected as closed
4. Closed positions appear in `recently_closed` output with `needs_experience_update: true` and full `position_snapshots` history
5. The entry is deleted from `known_positions.json`
6. Eva reflects on the trade, updates experience files
7. If no sell order found and expiry has passed → classified as "expired"

Positions with `reflected: false` are never treated as closed — they're new buys that haven't been confirmed by Tradier yet.

## Settlement

Cash account — funds from closed trades take 1 day to settle. Eva can only trade with `settled_cash`. If the sandbox reports `unsettled_funds` as 0, all cash is treated as settled.

## Data Delay

Tradier sandbox data is **15 minutes delayed**. Before ~9:45 AM ET, quotes reflect premarket and IV reads as 0%. The evaluate command guards against saving bad IV snapshots (skips if IV is 0), and the skill instructs Eva not to trade before 9:45 AM ET.

## Mode System

Every command accepts `--mode paper|real` (default: paper). Real mode exits with an error — it's a placeholder for future live trading. The architecture is mode-aware from day one so real trading plugs in cleanly.
