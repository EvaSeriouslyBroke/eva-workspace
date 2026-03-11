# Paper Trade Reflect Skill

**Skill name**: `paper-trade-reflect`
**Location**: `~/.openclaw/workspace/skills/paper-trade-reflect/SKILL.md`

Processes closed paper trades and creates/updates experience files. Runs in a dedicated session so Eva can focus entirely on reflection without the cognitive load of trading decisions.

---

## Trigger Phrases

- "reflect on trades"
- "process closed positions"
- "update experiences"
- Also triggered automatically by OpenClaw cron ~7 minutes after each evaluate cycle

---

## SKILL.md Content

```yaml
---
name: paper-trade-reflect
description: >
  Process recently closed paper trades and update experience files.
  Triggered by cron after evaluation cycles, or when asked to
  "reflect on trades", "process closed positions", "update experiences".
metadata:
  openclaw:
    emoji: "\U0001f4dd"
    requires:
      bins: ["python3"]
---
```

## Execution Flow

### 1. Load Context

Read experience system docs and strategy rules.

### 2. Fetch Pending Updates

```bash
python3 {baseDir}/../../options-toolkit/eva.py pending-experience
```

If the array is empty, skip to maintenance.

### 3. Process Each Closed Position

For each pending entry:
1. Analyze the trade outcome using all available data:
   - `open_reason` — why the trade was entered
   - `close_reason` — why it was closed
   - `closed_how` — sell_to_close or expired
   - `cost_basis` — what was paid
   - `entry_market_context` — market conditions at entry (price, IV, Greeks, trends with RSI/ATR/Bollinger/volume, IV rank/percentile, SPY context, news)
   - `position_snapshots` — full lifecycle: price, IV, Greeks at every evaluation cycle
   - `pre_sale_analysis` — hold-period summary: day-by-day option + stock trajectory, peak/trough during the hold with dates, P&L, and underlying stock price at those moments (`underlying_at_peak`, `underlying_at_trough`), whether Eva sold near the peak. Use this to assess exit timing — did the option peak mid-hold and decline before the sell? Did stock price movements explain the option's behavior?
   - For richer hold-period context, use the `market-snapshots` skill to see how trends, IV context, sentiment, and broader market conditions evolved between entry and exit.
   - `buy_entries` — all buys if the position was averaged into
2. Determine: was the thesis supported or contradicted? What happened to price, IV, and Greeks over the position's life? Did Eva exit at a good time or hold too long?
3. Consider all open questions from `PAPER.md` this trade speaks to — tag evidence with relevant questions even if the trade was originally motivated by only one
4. Determine market regime and DTE bucket at trade entry
5. Find or create the relevant experience file, add `[paper]` evidence entry
6. Follow the format, tagging, and evolution rules in `experience/README.md`

### 4. Clear Pending Updates

```bash
python3 {baseDir}/../../options-toolkit/eva.py pending-experience --clear
```

Only after all experience files are successfully written.

### 5. Experience Maintenance

Roll old evidence entries into Summary if Recent has more than 5. Look for cross-ticker patterns.

### 6. Report

Post a brief note about what was learned. Stay silent if nothing to process.

---

## Guardrails

- Does NOT make trading decisions
- Does NOT run `evaluate`, `buy`, or `sell`
- Focus only on experience creation, updates, and maintenance

---

## Scheduling

Runs via OpenClaw cron at `:07, :22, :37, :52` during market hours (7 minutes after each evaluate cycle at `:00, :15, :30, :45`). The evaluate job takes ~96 seconds, so 7 minutes provides ample buffer.

The pending file is durable — if the reflect skill fails or finds nothing, the data survives for the next cycle.
