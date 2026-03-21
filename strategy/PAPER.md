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
- Check news before trading. Understand whether the move has a fundamental
  driver or is noise.
- **Every buy must define a thesis with these components:**
  1. **What** — the pattern or catalyst you're trading on.
  2. **Time window** — when you expect the move to happen (e.g., "within 5
     trading days", "by March 25", "over the next 2-3 weeks"). Be specific.
     This is your patience horizon — you are committing to hold through noise
     within this window.
  3. **Expected move** — what you think the stock/contract will do and
     roughly how much upside you see (e.g., "stock recovers toward 50 SMA at
     260 — roughly +20% on the contract", "expect a $5-8 move higher on
     catalyst follow-through"). This is your initial theory of what success
     looks like, not a hard sell trigger. When the position reaches this
     zone, evaluate market conditions to decide whether to ride further or
     take profits.
  4. **Invalidation criteria** — what specific events or conditions would
     prove the thesis wrong (e.g., "breaks below 200 SMA", "negative earnings
     revision", "catalyst news retracted"). Price going down is NOT
     invalidation by itself — the thesis has to actually break.

### Exit
- **Thesis-driven exits only.** Do not sell because the price dipped. Sell
  because the thesis is no longer valid or because it played out.
- **Sell when:**
  - The expected move has played out and market conditions suggest the
    momentum is fading — take profits based on what you see (technicals,
    volume, news), not a fixed number.
  - The thesis is invalidated — a specific invalidation criterion was hit
    (news changed, key level broken, fundamental shift).
  - The time window expired and the expected move didn't happen — the thesis
    was wrong about timing, so cut and learn.
- **Do NOT sell when:**
  - The position is red but the time window hasn't expired and no
    invalidation criteria have been hit. This is noise, not failure.
  - The broader market dipped but your ticker-specific thesis is intact.
  - You "feel" like it's not working — check the criteria, not your gut.
- Track what made you exit and whether it was the right call.

### Averaging Down
- If a position dips **within the time window** and the thesis is still
  intact (no invalidation criteria hit), **consider averaging down** rather
  than selling. A lower price on the same thesis means a better entry.
- Before averaging down, re-check: Is the thesis still valid? Has any news
  changed? Are the fundamentals the same? If yes — the dip is an
  opportunity, not a reason to panic.
- Do not average down if an invalidation criterion has been hit. That's a
  sell, not a buying opportunity.

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
- **Added 2026-03-20:** NVDA hindsight confirms that holding short-DTE news plays without immediate confirmation leads to near 100% loss (-98.5%) due to accelerated theta and technical decay.

**Hypothesis:** Short-DTE news plays require immediate price confirmation. If the stock doesn't respond positively within the first trading day, the thesis is invalidated and early exit minimizes losses.

**Success Criteria:** After 10+ short-DTE news-driven trades, determine if entry-day price action is a reliable signal. If trades that close flat/down on entry day consistently lose money, establish "same-day exit" as a hard rule for this setup.

### News Persistence vs. Technical Exhaustion (2026-03-20)
**Source:** Hindsight — XLE260327C00057000 | **Status:** Active

**Goal:** Determine if structural fundamental news (e.g., War, Infrastructure Supply Shocks) provides a "Persistence Multiplier" that overrides technical exhaustion signals (RSI > 70).

**What to Test:**
- Identify trades where a major structural news catalyst is active (Supply-Risk Oil, Fraud, CEO Departure).
- When the RSI >70 + %B >100 signal triggers, compare outcomes between: (1) Exit immediately vs (2) Hold as long as headline catalyst persists.
- Track 3-day post-signal performance.
- Note if "Persistence" is sector-specific (e.g., Energy vs Tech).
- **Added 2026-03-20:** Energy sector (XLE) hindsight confirms that shorting based on RSI 73 during an active oil war results in an -80% loss. Fundamental persistence completely overrides technical gravity.

**Success Criteria:** If trades with structural catalysts continue to rise for 3+ days after technical exhaustion triggers in 60%+ of cases, create an "Elite News" exception rule for momentum exits.

### Catalyst vs. Trend Persistence (2026-03-20)
**Source:** Hindsight — QQQ260417P00595000 | **Status:** Active

**Goal:** Determine if trades aligned with an underlying technical trend should be held even after the original news catalyst fades.

**What to Test:**
- Identify trades where a technical trend (e.g., price below/above 50 SMA) is aligned with a temporary news catalyst (e.g., oil price spike).
- When the news catalyst fades (e.g., headlines calm down), check if the underlying remains in its technical regime.
- Compare outcomes: (1) Exit on catalyst fade vs (2) Hold as long as technical trend remains intact.
- **Evidence 2026-03-20:** QQQ Puts sold because "oil fears calmed" missed a 43% gain because technical weakness (below 50 SMA) persisted.

**Hypothesis:** If a news-driven entry is aligned with a structural technical trend, the trend will continue to drive price action even after the news is priced in or fades.

**Success Criteria:** If holding based on trend after catalyst fade produces 25%+ more P&L than immediate exit in 5+ trials, establish "Trend Alignment Priority" as a core rule.

### Yield Thresholds for Gold Hedges (2026-03-20)
**Source:** Hindsight — GLD260717C00470000 | **Status:** Active

**Goal:** Establish a hard rule for exiting gold/bullion hedges based on 10Y Treasury Yield movement to avoid capital wipes during macro shifts.

**What to Test:**
- Note 10Y Yield at time of bullish gold entry.
- Identify "Yield Resistance": a move of +10bps in 10Y yield over 24 hours.
- Test outcome if long GLD position is closed immediately upon hitting "Yield Resistance" vs holding for technical targets.
- **Evidence 2026-03-20:** Gold fell 7% in a week as yields rose toward 4.26%. Cutting on first yield spike would have saved the core of the position.

**Hypothesis:** Gold hedges are invalidated by rapid yield expansions regardless of current inflation headlines. The rate of change in yields is a higher-fidelity exit signal than the gold price itself.

**Success Criteria:** If yield-based exits preserve 20%+ more capital than thesis-based exits in 4+ instances, establish "Yield Cap" as a mandatory exit condition for gold calls.

### Momentum Shield Identification (2026-03-20)
**Source:** Hindsight — XLE260417P00059000 | **Status:** Active

**Goal:** Test if sector divergence (ticker green while SPY/QQQ is red) acts as a "Momentum Shield" that prevents mean-reversion pullbacks even when technical exhaustion (RSI > 70) is present.

**What to Test:**
- Identify when a stock reaches RSI > 70 + %B > 100.
- Check broad market status: (1) SPY Green vs (2) SPY Red.
- If SPY is Red while Ticker is Green (Divergence), test failure rate of short entries.
- **Evidence 2026-03-20:** Every XLE put attempt failed because XLE was in a bullish divergence during a tech crash.

**Hypothesis:** Shorting "overbought" stocks is a certain failure if they are exhibiting relative strength against a falling market. Divergence is a higher-conviction signal than RSI.

**Success Criteria:** If divergence-backed overbought stocks continue to rise for 3+ days in 70% of cases, establish "Divergence Trap" as a mandatory filter for avoiding BEARISH mean-reversion trades.

### Catalyst vs. Trend Persistence (2026-03-20)
**Source:** Hindsight — QQQ260417P00595000 | **Status:** Active

**Goal:** Determine if trades aligned with an underlying technical trend should be held even after the original news catalyst fades.

**What to Test:**
- Identify trades where a technical trend (e.g., price below/above 50 SMA) is aligned with a temporary news catalyst (e.g., oil price spike).
- When the news catalyst fades (e.g., headlines calm down), check if the underlying remains in its technical regime.
- Compare outcomes: (1) Exit on catalyst fade vs (2) Hold as long as technical trend remains intact.
- **Evidence 2026-03-20:** QQQ Puts sold because "oil fears calmed" missed a 43% gain because technical weakness (below 50 SMA) persisted.

**Hypothesis:** If a news-driven entry is aligned with a structural technical trend, the trend will continue to drive price action even after the news is priced in or fades.

**Success Criteria:** If holding based on trend after catalyst fade produces 25%+ more P&L than immediate exit in 5+ trials, establish "Trend Alignment Priority" as a core rule.

### News/Price Divergence in Downtrends (2026-03-20)
**Source:** Hindsight — BAC260717C00050000 | **Status:** Active

**Goal:** Test whether "Good News" coupled with "Bearish Price Action" is a high-confidence signal for an upcoming sharp leg down or continued stagnation.

**What to Test:**
- Identify when a ticker has a Bullish news sentiment score (e.g., >3) but the price is declining and below both 50/200 SMAs.
- Compare these instances to "Bearish News + Bearish Price."
- Track 3-day and 7-day price trajectory after the divergence appears.
- **Evidence 2026-03-20:** BAC had a +6 news score but a -88% options loss as price ignored fundamentals.

**Hypothesis:** Positive fundamentals are ignored in bear regimes. A divergence where "good news" fails to lift price is the ultimate bearish signal for that cycle.

**Success Criteria:** If price continues to decline or stay flat in 80% of divergence cases, establish "Divergence Trap" as a mandatory avoidance rule for mean reversion.

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

**Success Criteria:** If holding based on trend after catalyst fade produces 25%+ more P&L than immediate exit in 5+ trials, establish "Trend Alignment Priority" as a core rule.

### SMA Break Sensitivity (2026-03-20)
**Source:** Hindsight — QQQ260327C00600000 | **Status:** Active

**Goal:** Determine if immediate exit (within 1 hour) upon a decisive break of the 200-day SMA is a superior risk-management rule compared to waiting for a daily close.

**What to Test:**
- Identify when a stock in a recovery thesis touches its 200-day SMA from above.
- Record the price 1 hour after the touch and the end-of-day close.
- Compare outcomes: (1) Exit immediately vs (2) Exit at next daily close.
- **Evidence 2026-03-20:** QQQ continued to plummet after the 200 SMA break. Exiting within the breakdown day saved nearly 30% of the contract value on short-dated calls and 11% on LEAPs.

**Hypothesis:** Decisive breaks of the 200-day SMA on high volume characterize regime shifts that offer no immediate re-test opportunity. Immediate exit is safer than waiting for confirmation.

**Success Criteria:** If immediate exits save an average of 10%+ more capital across 5+ trades, promote "Hard SMA Floor" to a mandatory automated sell trigger.

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
