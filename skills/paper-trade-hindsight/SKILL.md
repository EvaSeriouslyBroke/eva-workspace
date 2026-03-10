---
name: paper-trade-hindsight
description: "Analyze closed paper trades with hindsight — compare sell decisions against what actually happened. Triggered weekly by cron or when asked to 'run hindsight analysis', 'review past sells', 'what if I held'."
metadata:
  openclaw:
    emoji: "\U0001f52e"
    requires:
      bins: ["python3"]
---

Hindsight analysis for closed paper trades. Compares sell decisions against actual outcomes. Follow every step in order.

## 1. Load Context

1. Read `{baseDir}/../../experience/README.md` — experience file format and rules
2. Read `{baseDir}/../../strategy/PAPER.md` — trading rules (for understanding trade theses)

## 2. Fetch Hindsight Data

```bash
python3 {baseDir}/../../options-toolkit/eva.py hindsight
```

Parse the JSON. If empty (`[]`), report "No closed watches to analyze" and stop.

## 3. Analyze Each Closed Watch

For each entry, evaluate the sell decision:

### Data Available

**Trade summary:**
- `sell_date`, `sell_price`, `sell_iv` — conditions at time of sale
- `cost_basis`, `sell_proceeds`, `realized_pnl` — what Eva actually got
- `open_reason` / `close_reason` — Eva's reasoning at entry and exit
- `entry_market_context` / `sell_market_context` — full market conditions at entry and exit

**Counterfactual (what-if-held):**
- `hold_to_now_value` / `hold_to_now_pnl` — current or final value vs cost
- `peak_value_after_sale` / `peak_date` — best possible exit after sale
- `trough_value_after_sale` / `trough_date` — worst point after sale
- `missed_upside` / `avoided_downside` — upside left vs downside dodged
- `sell_was_optimal` — did the sell beat holding to now?

**Daily trajectory** (`daily_trajectory`): Day-by-day post-sale summaries showing how the option evolved after Eva sold. Each day has:
- `bid_open`, `bid_high`, `bid_low`, `bid_close` — option price OHLC
- `iv_open`, `iv_close` — IV at start and end of day
- `underlying_close` — stock price at end of day
- `delta`, `theta` — close-of-day Greeks (directional exposure + time decay)
- `dte` — days to expiration remaining

Use the trajectory to spot: gradual trends vs sudden spikes, IV regime changes, theta acceleration near expiry, delta shifts as the option moves ITM/OTM.

**Key moment snapshots** (`key_moments`): Full snapshots (price, IV, all Greeks, underlying) at:
- `first_after_sell` — immediately after Eva sold
- `at_peak` — the moment the option hit its highest bid
- `at_trough` — the moment the option hit its lowest bid
- `latest` — most recent or final snapshot

Compare Greeks between these moments: did delta increase significantly (option went deeper ITM)? Did IV spike (news-driven)? Did theta accelerate (approaching expiry)?

**News around key dates** (`news_around_key_dates`): Headlines from the days around the sell date, peak date, and trough date (+/- 1 day). Use to identify catalysts — was the peak caused by a specific news event Eva could have anticipated? Was the trough driven by macro news or company-specific?

**Market around key dates** (`market_around_key_dates`): Stock price and IV environment on those same dates. Shows whether the underlying stock's IV was expanding or contracting, and where the stock price was relative to recent history.

### Investigation Process

For each trade, work through these questions using the trajectory and context data:

1. **Trajectory shape:** Look at `daily_trajectory`. Did the option price drift gradually, spike suddenly, or oscillate? A gradual trend suggests a predictable pattern. A sudden spike on one day suggests a catalyst — check `news_around_key_dates` for that date.

2. **Peak investigation:** Look at `key_moments.at_peak`. Compare its IV and delta to `sell_market_context`. If IV spiked, check news around the peak date — was there a catalyst? If delta increased significantly, the underlying moved toward the strike. Check `market_around_key_dates` for the peak date to see stock price and IV environment.

3. **Trough investigation:** Same analysis for the trough. If the trough came right after the sell, Eva's timing was good. If it came much later, what changed?

4. **IV trajectory:** Track `iv_open`/`iv_close` across the daily trajectory. Was IV expanding or contracting after the sell? If IV expanded significantly, a vol-based exit signal might have caught it.

5. **Thesis validation:** Compare `close_reason` to what actually happened. If Eva sold because "thesis played out", did the option actually decline after? If she sold on a stop-loss, did it recover? The trajectory shows this clearly.

6. **Luck vs skill:** If the peak coincides with a news event Eva couldn't have predicted (e.g., unexpected FDA approval, geopolitical event), that's luck — not a missed signal. If the peak followed a pattern Eva has seen before (e.g., IV expansion into earnings), that's a learnable lesson. Be honest.

### Priority: Expired Contracts

Focus most analysis on expired contracts (`expired: true`) — these have complete lifecycle data. Active watches get a lighter interim assessment.

## 4. Update Experiences

For each analyzed trade, update the experience system following the format and rules in `experience/README.md`:

1. Read `{baseDir}/../../experience/INDEX.md`
2. Find the experience file(s) related to this trade's pattern
3. Determine market regime and DTE bucket at trade entry (from `entry_market_context`)
4. Add a `[hindsight]` evidence entry — focus on:
   - Whether the sell timing was validated by subsequent price action
   - Key insight about what could have been done differently (or confirmation it was correct)
   - Any new pattern discovered from the post-sale data
   - Whether the outcome was regime-dependent
5. If this reveals a new pattern, create a new experience file and update INDEX.md

## 5. Clear Expired Watches

After processing all expired contracts:

```bash
python3 {baseDir}/../../options-toolkit/eva.py hindsight --clear-expired
```

Active (non-expired) watches remain for continued tracking.

## 6. Report

Post a Discord message summarizing findings:
- How many trades analyzed
- Key insights (sells that were validated, sells where holding was better, new patterns discovered)
- Any experience files created or updated

Stay silent if there were no watches to analyze.

## Guardrails

- This skill does NOT make trading decisions.
- This skill does NOT run `evaluate`, `buy`, or `sell`.
- Focus only on hindsight analysis, experience updates, and clearing expired watches.
- Be honest about luck vs skill. Not every outcome has a learnable lesson.
