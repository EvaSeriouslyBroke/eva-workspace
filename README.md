# Eva — Experience-Validated Autonomy

Eva is an autonomous options trading analyst that lives in Discord. She monitors markets, trades options in Tradier's paper trading sandbox, and builds a living knowledge base from every trade she makes.

## What Eva Does

Eva runs on a 15-minute cron cycle during market hours. Each cycle she:

- Fetches live market data, option chains, IV, Greeks, and news for her watchlist
- Evaluates open positions and detects closed trades
- Makes autonomous buy/sell/hold decisions based on her strategy and past experience
- Tracks position snapshots (price, IV, Greeks) over time for hindsight analysis
- Reports to the team via Discord

She also responds to interactive requests — price checks, option chains, full reports, portfolio status, and trade history.

## The Experience System

Eva's core differentiator is her thesis-based learning loop. Every trade generates evidence that feeds back into her decision-making.

**How it works:**

1. Eva observes a pattern (e.g., "IWM mean-reverts after 3%+ drops") and creates an experience file with a thesis, confidence level, and tags
2. Each time she encounters a similar setup, she recalls matching experiences before acting
3. Supporting trades strengthen the thesis; contradicting trades trigger analysis updates and exceptions
4. Over time, her experience files evolve from speculative observations into high-confidence, evidence-backed strategies

Experience files are living documents — the analysis section gets rewritten as understanding deepens, not appended to. Evidence is kept compact: the 5 most recent entries stay detailed, older ones are rolled into a summary. Nothing is deleted, even disproven theses, because knowing what *doesn't* work is valuable.

```
experience/
  INDEX.md           — Lookup table with one-line summaries, tags, confidence
  general/           — Market-wide patterns (IV crush, sentiment shifts, etc.)
  tickers/{TICKER}/  — Ticker-specific patterns
```

## Toolkit

Eva's CLI (`eva.py`) handles all market data fetching, option chain analysis, trade execution, and data persistence. Key commands:

- `evaluate` — Build evaluation JSON with market data, positions, IV context, affordable options
- `buy` / `sell` — Place orders through Tradier with full market context capture
- `status` — Portfolio overview
- `trade-history` — Order history merged with Eva's reasoning
- `report` — Scheduled market reports with IV tracking and comparison

## Trading Philosophy

Paper trading is the permanent laboratory. It runs continuously, taking highly speculative trades to generate experiences and build pattern knowledge. Every thesis — win or loss — feeds the experience system.

Real trading (when introduced) will only execute high-confidence theses that have been hardened through paper trading. If a strategy hasn't proven itself on paper first, it doesn't touch real capital. Paper trading never stops — it keeps running speculative plays in the background to expand the experience base, while real trading cherry-picks only what works.

## Stack

- **Python 3** — CLI and all analysis logic
- **Tradier API** — Market data, portfolio, order execution (sandbox for paper trading)
- **OpenClaw** — Agent framework, Discord integration, cron scheduling
- **yfinance + DuckDuckGo** — News headlines and deep article research
