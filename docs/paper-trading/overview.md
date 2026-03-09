# Paper Trading System — Overview

Eva trades options autonomously in Tradier's sandbox environment, building an experience knowledge base from every trade.

## Architecture

- **API**: Tradier sandbox (`https://sandbox.tradier.com/v1`) — handles portfolio, orders, market data
- **CLI**: `eva.py` — unified CLI with subcommands for evaluate, status, buy, sell, trade-history, reset
- **Strategy**: `strategy/PAPER.md` — mean reversion with news filter, 120+ DTE, max 10 positions
- **Experiences**: `experience/` — living theses refined by trade evidence
- **Skills**: 3 OpenClaw skills (evaluate, status, history) — 1 autonomous, 2 interactive
- **Cron**: Every 15 minutes during market hours via OpenClaw cron

## Data Isolation

Paper and real trading are fully isolated:
- **Config**: `tradier.json` has separate `paper` and `real` sections (only paper implemented)
- **API**: Sandbox URL vs live URL — never mixed
- **Local data**: `data/paper-trading/` vs `data/real-trading/` — separate directories
- **Discord**: Separate channels per mode

## Local Data (What Tradier Doesn't Store)

Tradier handles portfolio state, orders, and market data. We store only:
- `reasons.json` — maps Tradier order IDs to Eva's reasoning at trade time
- `known_positions.json` — tracks positions for closed-trade detection
- `log.jsonl` — append-only event log for debugging

## Closed Position Lifecycle

1. `buy` command writes position to `known_positions.json` with entry context
2. Each `evaluate` call diffs `known_positions.json` against Tradier's current positions
3. Missing positions = closed (sold, expired, or assigned)
4. Closed positions appear in `recently_closed` output with `needs_experience_update: true`
5. Eva reflects on the trade, updates experience files
6. Position marked as "reflected" — no longer appears in `recently_closed`
7. If no sell order found and expiry has passed → classified as "expired"

## Settlement

Cash account — funds from closed trades take 1 day to settle. Eva can only trade with `settled_cash`. If the sandbox reports `unsettled_funds` as 0, all cash is treated as settled.

## Data Delay

Tradier sandbox data is **15 minutes delayed**. Before ~9:45 AM ET, quotes reflect premarket and IV reads as 0%. The evaluate command guards against saving bad IV snapshots (skips if IV is 0), and the skill instructs Eva not to trade before 9:45 AM ET.

## Mode System

Every command accepts `--mode paper|real` (default: paper). Real mode exits with an error — it's a placeholder for future live trading. The architecture is mode-aware from day one so real trading plugs in cleanly.
