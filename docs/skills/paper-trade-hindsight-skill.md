# Paper Trade Hindsight Skill

**Skill name**: `paper-trade-hindsight`
**Location**: `~/.openclaw/workspace/skills/paper-trade-hindsight/SKILL.md`

Analyzes closed paper trades with hindsight — compares sell decisions against what actually happened. Runs weekly after market close or on-demand.

---

## Trigger Phrases

- "run hindsight analysis"
- "review past sells"
- "what if I held"
- Also triggered automatically by OpenClaw cron weekly on Fridays at 4:15 PM ET

---

## SKILL.md Content

```yaml
---
name: paper-trade-hindsight
description: >
  Analyze closed paper trades with hindsight — compare sell decisions against
  what actually happened. Triggered weekly by cron or when asked to
  "run hindsight analysis", "review past sells", "what if I held".
metadata:
  openclaw:
    emoji: "\U0001f52e"
    requires:
      bins: ["python3"]
---
```

## Execution Flow

### 1. Load Context

Read experience system docs and strategy rules.

### 2. Fetch Hindsight Data

```bash
python3 {baseDir}/../../options-toolkit/eva.py hindsight
```

If empty, report nothing to analyze and stop.

### 3. Analyze Each Closed Watch

For each entry, investigate the full lifecycle — both during the hold and after the sell:
- **Pre-sale analysis** — day-by-day option trajectory during the hold, peak/trough with dates, P&L, and underlying stock price at those moments. Shows whether there was a better exit before the actual sell.
- **Hold-period stock context** — what the STOCK did during the hold: daily OHLCV trajectory, RSI/ATR/Bollinger/SMA indicators computed at entry, option peak, option trough, and sell. Shows whether stock signals should have triggered an earlier exit.
- **Entry/sell market context** — full snapshots at both entry and exit: trends (RSI, ATR, Bollinger, SMAs, prev day high/low, avg volume), IV context (rank, percentile, 52w range), broader market (SPY). Compare to see how conditions shifted.
- **Stock context** — what the STOCK did post-sale: daily OHLCV trajectory, volume vs 50-day average, and technical indicators (RSI, ATR, Bollinger %B, SMAs) computed at sell, peak, trough, and latest. Shows whether the stock was oversold and bounced, or kept falling as expected.
- **Daily trajectory** — day-by-day post-sale option price OHLC, IV, delta, theta, and stock price OHLC + volume. Spot gradual trends vs sudden spikes, IV regime changes, theta acceleration. Stock OHLC shows whether stock moves drove option changes.
- **Key moment snapshots** — full Greeks/IV/prices at peak, trough, and boundaries. Compare to sell-time context to understand what changed.
- **Counterfactual** — realized P&L vs hold-to-now, peak/trough values (with underlying stock price at each), missed upside, avoided downside.
- **News around key dates** — headlines near the sell, peak, and trough dates. Identify catalysts — was a peak caused by predictable news or a surprise?
- **Market around key dates** — stock price and IV environment at those moments.
- For richer context around key dates, use the `market-snapshots` skill to browse detailed snapshots near the sell, peak, or trough, or find price/IV extremes over a wider window.

### Investigation Process

For each trade, work through these questions using the trajectory and context data:

1. **Trajectory shape:** Look at `daily_trajectory`. Did the option price drift gradually, spike suddenly, or oscillate? A gradual trend suggests a predictable pattern. A sudden spike on one day suggests a catalyst — check `news_around_key_dates` for that date.

2. **Peak investigation:** Look at `key_moments.at_peak`. Compare its IV and delta to `sell_market_context`. If IV spiked, check news around the peak date — was there a catalyst? If delta increased significantly, the underlying moved toward the strike. Check `market_around_key_dates` for the peak date to see stock price and IV environment.

3. **Trough investigation:** Same analysis for the trough. If the trough came right after the sell, Eva's timing was good. If it came much later, what changed?

4. **IV trajectory:** Track `iv_open`/`iv_close` across the daily trajectory. Was IV expanding or contracting after the sell? If IV expanded significantly, a vol-based exit signal might have caught it.

5. **Pre-sale trajectory:** Look at `pre_sale_analysis`. Did the option peak mid-hold and then decline? If `sold_near_peak` is false and `peak_pnl_pct` is significantly higher than `realized_pnl_pct`, Eva held too long. Compare the pre-sale daily trajectory's IV and delta shifts to spot the turning point. If the option was volatile during the hold with large bid swings, consider whether tighter exit criteria would have captured more profit.

6. **Stock technical context:** Look at `stock_context.indicators_at_key_dates`. Compare RSI, ATR, Bollinger %B at sell vs at peak/trough. If RSI was 28 at sell and climbed to 55 at peak, the stock was oversold and bounced — a signal Eva could have read. If RSI was 65 at sell and dropped to 25 at trough, the sell was well-timed. Check if volume spiked after the sell (`stock_trajectory` daily volume vs `avg_volume_50d`).

7. **Thesis validation:** Compare `close_reason` to what actually happened. If Eva sold because "thesis played out", did the option actually decline after? If she sold on a stop-loss, did it recover? The trajectory shows this clearly.

8. **Luck vs skill:** If the peak coincides with a news event Eva couldn't have predicted (e.g., unexpected FDA approval, geopolitical event), that's luck — not a missed signal. If the peak followed a pattern Eva has seen before (e.g., IV expansion into earnings), that's a learnable lesson. Be honest.

### Priority: Expired Contracts

Focus most analysis on expired contracts (`expired: true`) — these have complete lifecycle data. Active watches get a lighter interim assessment.

### 4. Update Experiences

Add `[hindsight]` evidence entries to relevant experience files following the rules in `experience/README.md`. Consider all open questions from `PAPER.md` each trade speaks to — tag evidence with relevant questions and create/update experience files for each, even if the trade was originally motivated by only one. Create new experiences if post-sale patterns were discovered.

### 5. Clear Expired Watches

```bash
python3 {baseDir}/../../options-toolkit/eva.py hindsight --clear-expired
```

### 6. Report

Post Discord summary of findings.

---

## Guardrails

- Does NOT make trading decisions
- Does NOT run `evaluate`, `buy`, or `sell`
- Focus only on hindsight analysis and experience updates

---

## Scheduling

Runs via OpenClaw cron weekly on Fridays at 4:15 PM ET. This timing ensures:
- Full week of post-sale data accumulated
- After market close (no stale intraday data)
- After the final evaluate/reflect cycle of the week
