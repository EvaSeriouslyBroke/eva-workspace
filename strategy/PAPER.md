# Paper Trading Strategy

## Purpose

Day trade weekly options. Learn which intraday setups produce profitable trades.
Every trade is data — wins show what works, losses teach what to avoid.

## Open Questions

1. **Intraday Entry Timing** — What signals indicate the best time to enter a
   day trade? Morning momentum, midday reversals, late-day trends?
2. **Profit-Taking Timing** — When is the optimal time to close a winning
   position? How much of a move should you capture before exiting?
3. **Reversal Detection** — What signals reliably indicate a trend reversal is
   underway? How early can you catch it?

## Core Approach: Day Trading Weeklies with the Trend

Buy and sell options within the same trading day using the nearest 2 weekly
expirations. Trade with the trend: calls in bull markets, puts in bear markets.
When a reversal is forming, trade the direction stocks are heading — not where
they've been.

## Rules

### Direction Rule
- **Bull market → calls only.** If the trend is up (price above 50 SMA, SPY
  green, positive momentum), only buy calls.
- **Bear market → puts only.** If the trend is down (price below 50 SMA, SPY
  red, negative momentum), only buy puts.
- **Reversal → trade the new direction.** When signals indicate a reversal
  (momentum shift, SMA crossover forming, divergence between price and
  indicators, volume surge against the trend), buy in the direction stocks are
  headed. If a bull stock is rolling over, buy puts. If a bear stock is
  bottoming, buy calls.

### How to Determine Market Direction
Use multiple signals — no single indicator is enough:
- **SMA position:** price above 50 SMA = bullish bias, below = bearish bias
- **SPY context:** SPY green and trending up = bull market backdrop
- **Intraday momentum:** is the stock making higher highs or lower lows today?
- **Recent days:** last 3-5 daily candles — trending up or down?
- **RSI:** >60 favors calls, <40 favors puts, 40-60 is neutral (look for
  other signals)
- **News sentiment:** bullish catalysts support calls, bearish support puts

### What's On the Table
- **Weeklies only** — only the nearest 2 weekly expirations. High gamma means
  big sensitivity to price moves, which is what day trades need.
- **Calls or puts** — based on market direction per the direction rule above.
- **Any intraday setup** — momentum, mean reversion, news-driven, technical
  breakouts, opening range plays — find what works.
- **Multiple simultaneous trades** — test different setups across tickers.
- **No position count limits** — trade as much as settled cash allows.

### Hard Constraints
- **Day trades only** — every position opened today must be closed today. No
  overnight holds, no exceptions.
- **Only settled cash** — unsettled funds take 1 day to clear.
- **No far OTM options** — stick to strikes with meaningful delta
  (|delta| >= 0.20).
- **Close everything by 3:45 PM ET** — don't risk getting stuck at close.
  Start closing at 3:30 PM if needed.

### Entry
- Check market direction first. Determine if this is a bull or bear environment
  for the ticker and broader market.
- Use all available data: price action, Greeks, IV rank, intraday OHLC, volume,
  news, SPY context, recent daily candles.
- Prefer high gamma options (near-money, short DTE) — they move more with the
  underlying.
- Watch for: momentum surges, volume spikes, news catalysts, support/resistance
  bounces, opening gaps, sector rotation signals.
- **Every buy must define a thesis:**
  1. **Direction** — bull or bear, and why (trend indicators, news, SPY).
  2. **What** — the intraday pattern or catalyst you're trading on.
  3. **Expected move** — what you think the stock will do intraday and roughly
     how much profit you're targeting.
  4. **Invalidation** — what would prove the intraday thesis wrong (e.g.,
     "breaks below VWAP", "SPY reverses", "fails to hold morning gap").
  5. **Exit plan** — when you plan to sell (target hit, time stop, by 3:30 PM).

### Exit
- **Take profits when they're there.** Day trades are about capturing moves,
  not holding for max gain. If your target is hit, sell.
- **Cut losses quickly.** If the thesis is wrong, don't wait. A small loss
  beats a big one.
- **Sell when:**
  - Target profit reached — take it.
  - Thesis invalidated — the setup broke, cut the loss.
  - Direction reverses — if you're in calls and the stock starts trending
    down (or vice versa), exit and potentially reverse.
  - Time decay — if the trade hasn't moved in your favor within a reasonable
    window (30-60 min), consider exiting.
  - Approaching 3:45 PM — close everything regardless of P&L.
- **Do NOT hold overnight.** Period.

### Learning Priority
- **Volume of trades.** More trades = more data about what works.
- **Document everything.** Entry reasoning, exit reasoning, what you saw.
- **Track direction accuracy.** How often is your bull/bear read correct?
  What signals were most reliable?
- **Track reversal detection.** When you caught a reversal, what tipped you
  off? When you missed one, what signal did you ignore?
- **Compare setups.** Which types of day trades produce the most consistent
  profits? Morning momentum vs afternoon reversals? News-driven vs technical?
- **Learn from losses.** Was the direction wrong? Was the entry too late?
  Did you hold too long?

## Testing

### Day Trade Setup Discovery (2026-03-24)
**Source:** Kydio | **Status:** Active

**Goal:** Find which intraday setups consistently produce profitable day trades
with weekly options, following the trend direction.

**What to Test:**
- Morning momentum plays with trend (first 30-60 min)
- Reversal entries when indicators diverge from price
- News-driven intraday moves (calls on bullish news, puts on bearish)
- Gap plays aligned with trend direction
- Volume surge entries confirming direction
- How accurate are the direction signals? (SMA, SPY, RSI, momentum)
- When to flip direction mid-day if reversal signals appear

**Track:**
- Entry time, exit time, hold duration
- Direction call (bull/bear) and whether it was correct
- Setup type (momentum, reversal, gap, news, technical)
- Which weekly expiration used (nearest vs next)
- P&L per trade
- Which tickers produce the best day trades
- Time of day patterns

**Success Criteria:** After 20+ day trades, identify which 2-3 setup types
produce the most consistent profits and which direction signals are most
reliable. Build a playbook of repeatable intraday patterns.
