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

### Market Regime Tagging (2026-03-11)
**Source:** Kydio | **Status:** Always Active

**Goal:** Do strategies behave differently in bull vs bear markets, or during turning points? Find out by tagging every trade.

**What to Test:**
- Try the same strategy types across different market regimes
- Compare outcomes of identical setups in bull vs bear conditions
- Pay attention to transitions — do strategies break during turning points?

Tag definitions and rules are in `experience/README.md` (Required Tags section).

**Success Criteria:** After accumulating trades across different regimes, compare win rates and outcomes for the same strategy in different regimes. Let the data reveal which strategies are regime-dependent.

---

### DTE Experimentation (2026-03-11)
**Source:** Kydio | **Status:** Active

**Goal:** How do different DTE ranges affect outcomes for different strategy types? Find out by testing across short, medium, and long timeframes.

**What to Test:**
- Try mean reversion, momentum, news-driven, and other strategies at each DTE bucket
- Compare how theta decay, gamma exposure, and IV changes affect outcomes at different DTEs
- Test whether hold time correlates with DTE choice or strategy type

DTE bucket definitions are in `experience/README.md` (Required Tags section).

**Success Criteria:** After 10+ trades per DTE bucket, compare results by strategy type within each bucket. No assumptions about which DTE works for what — let the numbers show it.
