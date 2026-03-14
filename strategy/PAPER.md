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

### Entry-Day Momentum Validation for Short-DTE News Plays (2026-03-14)
**Source:** Hindsight — NVDA260325C00190000 | **Status:** Active

**Goal:** Test whether immediate price response to news is a reliable predictor of success for short-DTE (<15 days) momentum trades.

**What to Test:**
- Enter calls on news catalysts with 10-15 DTE
- Track stock price movement within first 4 hours of entry day
- If stock closes flat or down on entry day, exit immediately next morning vs holding
- Compare outcomes: immediate exit (same/next day) vs holding 2-3 days waiting for momentum
- Note correlation between entry-day price action and ultimate trade outcome
- Test if "offsetting news" (competitor announcements, market weakness) neutralizes catalysts

**Hypothesis:** Short-DTE news plays require immediate price confirmation. If the stock doesn't respond positively within the first trading day, the thesis is invalidated and early exit minimizes losses.

**Success Criteria:** After 10+ short-DTE news-driven trades, determine if entry-day price action is a reliable signal. If trades that close flat/down on entry day consistently lose money, establish "same-day exit" as a hard rule for this setup.

### RSI >70 + Bollinger %B >100 Profit-Taking Validation (2026-03-14)
**Source:** Hindsight — XLE260327C00057000 | **Status:** Active

**Goal:** Validate whether the RSI >70 + Bollinger %B >100 technical exhaustion signal reliably marks near-term peaks across multiple tickers and momentum setups.

**What to Test:**
- Enter momentum continuation trades (calls on uptrending stocks, sector rotation plays, news-driven momentum)
- Hold until either: (a) RSI >70 AND Bollinger %B >100, or (b) 3 days elapsed, or (c) -20% loss
- Compare outcomes between "sell at exhaustion signal" vs "hold for extended gains"
- Test across different sectors: energy (XLE), tech (QQQ, NVDA), financials (BAC), small-caps (IWM)
- Track how quickly prices decline after the signal triggers (same day, next day, or doesn't decline)

**Hypothesis:** The combination of RSI >70 (momentum exhaustion) and Bollinger %B >100 (statistical extreme) provides a reliable near-term peak signal for momentum trades. Exiting on this signal captures optimal gains before mean reversion begins.

**Success Criteria:** After 8+ momentum trades across 3+ different tickers, if 75%+ of exits at RSI >70 + %B >100 are followed by price declines within 24-48 hours, promote this signal to a core profit-taking rule. If success rate is <50%, the signal is not reliable enough for systematic use.

### Catalyst Fade vs Independent Drivers Test (2026-03-14)
**Source:** Hindsight — QQQ260417P00595000 | **Status:** Active

**Goal:** Determine whether to exit directional trades when the original catalyst fades, or hold if the underlying has independent technical drivers.

**What to Test:**
- Enter puts on news-driven bearish setups (geopolitical fear, sector rotation, earnings warnings)
- Track both: (a) catalyst strength (headlines, sentiment shifts) AND (b) underlying technicals (trend, SMA position, RSI momentum)
- When catalyst fades (e.g., oil fears ease), check if underlying is below 50 SMA with negative momentum
- Compare outcomes: "exit on catalyst fade" vs "hold if independent bearish drivers exist"
- Test across QQQ, IWM, SPY, XLE, sector ETFs

**Hypothesis:** Exiting solely because the catalyst fades is a mistake when the underlying has independent bearish drivers (below 50 SMA, negative momentum, poor sector dynamics). The catalyst and the trend are separate — one fading doesn't invalidate the other.

**Success Criteria:** After 6+ trades where catalyst fades but underlying remains technically weak, if holding produces better outcomes than exiting in 60%+ of cases, establish "check independent drivers before exiting" as a core rule. Track P&L difference between early exit vs holding for technical targets.
