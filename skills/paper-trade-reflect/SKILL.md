---
name: paper-trade-reflect
description: "Process recently closed paper trades and update experience files. Triggered by cron after evaluation cycles, or when asked to 'reflect on trades', 'process closed positions', 'update experiences'."
metadata:
  openclaw:
    emoji: "\U0001f4dd"
    requires:
      bins: ["python3"]
---

Process pending experience updates from closed paper trades. Follow every step in order.

## 1. Load Context

1. Read `{baseDir}/../../experience/README.md` — experience file format and rules
2. Read `{baseDir}/../../strategy/PAPER.md` — trading rules (for understanding trade theses)

## 2. Fetch Pending Updates

```bash
python3 {baseDir}/../../options-toolkit/eva.py pending-experience
```

Parse the JSON array. If empty (`[]`), skip to step 5.

## 3. Process Each Closed Position

For each entry with `needs_experience_update: true`:

1. Read `{baseDir}/../../experience/INDEX.md`
2. Analyze the trade outcome using all available data:
   - `open_reason` — why the trade was entered
   - `close_reason` — why it was closed
   - `closed_how` — sell_to_close or expired
   - `cost_basis` — what was paid
   - `entry_market_context` — market conditions at entry (price, IV, Greeks, trends with RSI/ATR/Bollinger/volume, IV rank/percentile, SPY context, news)
   - `position_snapshots` — full lifecycle: price, IV, Greeks at every evaluation cycle
   - `pre_sale_analysis` — hold-period summary: day-by-day option + stock trajectory, peak/trough during the hold with dates, P&L, and underlying stock price at those moments (`underlying_at_peak`, `underlying_at_trough`), whether Eva sold near the peak. Use this to assess exit timing — did the option peak mid-hold and decline before the sell? Did stock price movements explain the option's behavior?
   - `buy_entries` — all buys if the position was averaged into
3. Determine: was the thesis supported or contradicted? What happened to price, IV, and Greeks over the position's life? Did Eva exit at a good time or hold too long?

   **Historical context:** If you need to understand what the broader market was doing during the hold, or find peaks/troughs around the trade dates, use the `market-snapshots` skill. It can show trends, IV context, sentiment, and broader market conditions for any date range.
4. Consider all open questions from `{baseDir}/../../strategy/PAPER.md` this trade speaks to — tag evidence with relevant questions and create/update experience files for each, even if the trade was originally motivated by only one
5. Determine market regime and DTE bucket at trade entry (see `experience/README.md` for tag definitions)
6. Find or create the relevant experience file — follow the evolution rules and evidence format in `experience/README.md`
7. If a new experience file was created, add it to `{baseDir}/../../experience/INDEX.md`

## 4. Clear Pending Updates

After ALL experience files have been successfully created/updated:

```bash
python3 {baseDir}/../../options-toolkit/eva.py pending-experience --clear
```

Only clear after everything is written. If you fail partway through, the data survives for the next cycle.

## 5. Experience Maintenance

Review any experience files you touched:
- If the Recent evidence section has more than 5 entries, roll the oldest into the Summary
- Look for cross-ticker patterns worth noting in `general/`

If there were no pending updates and no maintenance needed, stay silent.

## 6. Report

- If experiences were created or updated, post a brief note to Discord about what was learned.
- Stay silent if there was nothing to process.

## Guardrails

- This skill does NOT make trading decisions.
- This skill does NOT run `evaluate`, `buy`, or `sell`.
- Focus only on experience creation, updates, and maintenance.
