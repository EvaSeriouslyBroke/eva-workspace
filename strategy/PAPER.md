# Paper Trading Strategy

## Purpose

Experiment freely. Find patterns. Build confidence through volume. Every trade
is data — wins teach what works, losses teach what doesn't.

## Open Questions

Core questions Eva is trying to answer through trading. Every trade can — and
often does — provide evidence for multiple questions simultaneously.

1. **Catching a Falling Knife** — What signals distinguish a stock that will
   keep falling from one that is near its bottom?
2. **Bounce-Back Signals** — After a significant drop, what tells us a
   recovery is coming?
3. **Bearish Reversal Detection** — When a stock is rising, what signals
   indicate it's about to drop or enter a bearish stretch?

Use all available data — price action, Greeks, IV, volume, news, and general
stock price context — to build evidence toward these questions. Tag trades
with all relevant questions in your reasoning.

## Core Approach: Unrestricted Experimentation

Eva has full freedom to explore any strategy, any timeframe, any thesis.
The goal is pattern recognition across as many market conditions as possible.

## Rules

### What's On the Table
- **Any DTE** — weeklies, monthlies, LEAPs, anything. Short-term plays welcome.
- **Any strategy** — mean reversion, momentum, earnings plays, news-driven,
  technical breakouts, volatility plays, whatever Eva sees a pattern in.
- **Multiple simultaneous theses** — test different ideas at the same time.
  Compare which patterns hold up and which don't.
- **No position count limits** — trade as much as settled cash allows.
- **Any position size** — one contract is fine. Multiple contracts is fine.

### Hard Constraints
- **Only settled cash** — unsettled funds take 1 day to clear.
- **No far OTM options** — only buy near-the-money or slightly OTM. Far OTM
  options have terrible odds and decay fast. Stick to strikes with meaningful
  delta (roughly |delta| >= 0.20).

### Entry
- Use all available data: price action, Greeks, IV rank, trends, news,
  historical patterns, volume, open interest — the full picture.
- Document the thesis clearly. What pattern are you seeing? What do you
  expect to happen and why? What would prove you wrong?
- Check news before trading. Understand whether the move has a fundamental
  driver or is noise.

### Exit
- Re-evaluate every position each cycle.
- Sell when the thesis has played out, is clearly wrong, or conditions change.
- No hard stop-loss percentages — use judgment based on the full picture.
- Track what made you exit and whether it was the right call.

### Learning Priority
- **Trade more, not less.** Volume of trades = volume of data.
- **Document everything.** Rich reasoning at entry and exit feeds the
  experience system.
- **Reflect after every close.** Update the relevant experience with what
  happened and why.
- **Look for cross-ticker patterns.** Does something that works for IWM
  also work for SPY? Record it.
- **Test edge cases.** Trade into earnings, trade on Fed days, trade on
  low IV — find out where patterns break down.

## Testing

User-suggested or Eva-proposed experiments under evaluation.
Add entries here with the date and source. Promote to core knowledge or
remove based on paper trading results.

### 2-Week DTE Profitability (2026-03-11)
**Source:** Kydio | **Status:** Active

**Goal:** Focus on buying options with ~2 weeks (10-14 calendar days) to expiration and figure out how to consistently turn a profit with them.

**What to Test:**
- Buy calls and puts in the 10–14 DTE range across all tracked tickers
- Experiment with entry timing — is it better to enter on dips, breakouts, or mean reversion setups?
- Test strike selection — how does ATM vs slightly OTM affect outcomes at this DTE?
- Track how theta decay impacts holds — is there a sweet spot for how long to hold before decay kills the position?
- Compare quick flips (1–3 day holds) vs riding the full 2 weeks
- Note which market conditions (trending, choppy, high IV, low IV) produce the best results at this DTE

**Success Criteria:** After 15+ trades in the 10–14 DTE range, identify which setups, hold times, and market conditions produce profitable outcomes. Build a repeatable playbook for 2-week options.
