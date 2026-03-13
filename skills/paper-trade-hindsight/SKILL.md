---
name: paper-trade-hindsight
description: "Analyze a single closed paper trade with hindsight — compare sell decision against what actually happened. Dispatched per-symbol by run_hindsight.sh or on-demand."
metadata:
  openclaw:
    emoji: "\U0001f52e"
    requires:
      bins: ["python3"]
---

Hindsight analysis for a single closed paper trade. Each invocation analyzes exactly ONE symbol, passed in the trigger message. Follow every step in order.

## 1. Extract Symbol

The trigger message contains the OCC symbol to analyze (e.g., "Run hindsight analysis for NVDA260325C00190000"). Extract it.

## 2. Load Context

1. Read `{baseDir}/../../experience/README.md` — experience file format and rules
2. Read `{baseDir}/../../strategy/PAPER.md` — trading rules and open questions

## 3. Fetch Hindsight Data

```bash
python3 {baseDir}/../../options-toolkit/eva.py hindsight --symbol {SYMBOL}
```

Parse the JSON. If error, report and stop.

## 4. Analyze the Trade

### Core Questions

Work through these using the full data (trajectories, context, news, Greeks):

**1. Sell timing — was it right?**
- Look at `daily_trajectory` and `counterfactual`. Did the option keep declining after the sell (good timing) or rally (bad timing)?
- Compare `sell_market_context` to `key_moments.at_peak`. What changed — IV, delta, underlying price?
- Check `pre_sale_analysis`. Did the option peak mid-hold? If `sold_near_peak` is false and `peak_pnl_pct` >> `realized_pnl_pct`, Eva held too long.

**2. Could Eva have sold at a better price?**
- Look at `pre_sale_analysis.daily_trajectory` for the hold period. Were there clear peaks she missed?
- Check `hold_stock_context.indicators_at_key_dates`. Did RSI, Bollinger, or volume signal an exit before the actual sell?
- Was there a day where IV spiked (check `iv_open`/`iv_close` in trajectory) that would have been a better exit?

**3. Could Eva have rebought after selling?**
- Look at `daily_trajectory` post-sale. Did the option drop significantly after the sell, creating a rebuy opportunity?
- Check `counterfactual.trough_value_after_sale` — how low did it go? If it dropped substantially then recovered, there was a rebuy window.
- What were the indicators at the trough? Check `key_moments.at_trough` and `stock_context.indicators_at_key_dates.at_trough` — RSI oversold? Bollinger near lower band? Volume spike?

**4. What indicators would have helped?**
- Compare indicators at entry, peak, trough, and sell across both `hold_stock_context` and `stock_context`. Which ones predicted the turns?
- Did news events drive the peaks/troughs? Check `news_around_key_dates`. Predictable catalysts vs surprises.
- Track IV trajectory (`iv_open`/`iv_close` across days). Did IV expansion/contraction predict price moves?
- Was theta decay the dominant force, or were delta/IV moves larger?

**5. Luck vs skill — be honest**
- If the peak coincides with an unpredictable news event, that's luck — not a missed signal.
- If the pattern was something Eva has seen before (e.g., RSI oversold bounce, IV expansion into event), that's a learnable lesson.

### Data Available

**Trade summary:**
- `sell_date`, `sell_price`, `sell_iv` — conditions at time of sale
- `cost_basis`, `sell_proceeds`, `realized_pnl` — what Eva actually got
- `open_reason` / `close_reason` — Eva's reasoning at entry and exit
- `entry_market_context` / `sell_market_context` — full market conditions at entry and exit, including trends (RSI, ATR, Bollinger, SMAs, prev day high/low, avg volume), IV context (rank, percentile, 52w range), and broader market (SPY price + change)

**Counterfactual (what-if-held):**
- `hold_to_now_value` / `hold_to_now_pnl` — current or final value vs cost
- `peak_value_after_sale` / `peak_date` — best possible exit after sale
- `trough_value_after_sale` / `trough_date` — worst point after sale
- `missed_upside` / `avoided_downside` — upside left vs downside dodged
- `sell_was_optimal` — did the sell beat holding to now?

**Pre-sale analysis** (`pre_sale_analysis`): What happened during the hold — was there a better exit before the actual sell?
- `daily_trajectory` — day-by-day option OHLC, IV, Greeks during the hold period (including stock OHLC)
- `peak_bid` / `peak_date` / `peak_value` / `peak_pnl` / `peak_pnl_pct` — the best exit point during the hold
- `underlying_at_peak` — stock price when the option peaked
- `trough_bid` / `trough_date` / `trough_value` — worst point during the hold
- `underlying_at_trough` — stock price when the option troughed
- `sold_near_peak` — whether Eva sold within 5% of the hold-period peak

**Hold-period stock context** (`hold_stock_context`): What the STOCK did during the hold (entry → sell).
- `stock_trajectory` — daily OHLCV of the underlying during the hold period
- `avg_volume_50d` — 50-day average volume as of entry
- `indicators_at_key_dates` — RSI, ATR, Bollinger %B, SMA 50/200 at: entry, option peak, option trough, sell

**Daily trajectory** (`daily_trajectory`): Day-by-day post-sale summaries.
- `bid_open`, `bid_high`, `bid_low`, `bid_close` — option price OHLC
- `iv_open`, `iv_close` — IV at start and end of day
- `underlying_open`, `underlying_high`, `underlying_low`, `underlying_close` — stock price OHLC
- `underlying_volume` — stock volume (when available)
- `delta`, `theta` — close-of-day Greeks
- `dte` — days to expiration remaining

**Stock context** (`stock_context`): What the STOCK did after the sell.
- `stock_trajectory` — daily OHLCV from sell date onward
- `avg_volume_50d` — 50-day average volume at time of sale
- `indicators_at_key_dates` — RSI, ATR, Bollinger %B, SMA 50/200 at sell, peak, trough, latest

**Key moment snapshots** (`key_moments`): Full snapshots (price, IV, all Greeks, underlying) at `first_after_sell`, `at_peak`, `at_trough`, `latest`.

**News around key dates** (`news_around_key_dates`): Headlines near the sell, peak, and trough dates (+/- 1 day).

**Market around key dates** (`market_around_key_dates`): Stock price and IV environment at those dates.

**Deeper snapshot context:** Use the `market-snapshots` skill for richer context around specific dates if needed.

### Priority: Expired Contracts

Focus most analysis on expired contracts (`expired: true`) — these have complete lifecycle data. Active watches get a lighter interim assessment.

## 5. Update Experiences

Follow the format and rules in `experience/README.md`:

1. Read `{baseDir}/../../experience/INDEX.md`
2. Find related experience file(s) for this trade's pattern
3. Consider all open questions from PAPER.md this trade speaks to — tag evidence with relevant questions
4. Determine market regime and DTE bucket at trade entry (from `entry_market_context`)
5. Add a `[hindsight]` evidence entry focused on:
   - Whether the sell timing was validated by subsequent price action
   - Rebuy opportunities that existed (or didn't)
   - Indicator signals that predicted the post-sale moves
   - Whether the outcome was regime-dependent
6. If this reveals a new pattern, create a new experience file and update INDEX.md

## 6. Propose Tests

If the analysis reveals a testable hypothesis (e.g., "RSI < 30 at sell → option bounces within 3 days", "IV spike > 20% from entry → take profits"), add it to the `## Testing` section of `{baseDir}/../../strategy/PAPER.md` using the existing format:

```
### Test Name (YYYY-MM-DD)
**Source:** Hindsight — {SYMBOL} | **Status:** Active

**Goal:** ...
**What to Test:** ...
**Success Criteria:** ...
```

Only add tests for specific, actionable hypotheses with clear success criteria. Not every trade produces a test.

## 7. Report

Post a Discord message summarizing:
- Trade analyzed (symbol, ticker, P&L)
- Sell timing verdict
- Rebuy opportunities identified
- Key indicator signals discovered
- Experience files created or updated
- Any new tests added to PAPER.md

## Guardrails

- This skill does NOT make trading decisions.
- This skill does NOT run `evaluate`, `buy`, or `sell`.
- Focus only on hindsight analysis, experience updates, and proposing tests.
- Be honest about luck vs skill. Not every outcome has a learnable lesson.
