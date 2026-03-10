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

For each entry, investigate what happened after the sell using:
- **Daily trajectory** — day-by-day option price OHLC, IV, delta, theta, underlying price. Spot gradual trends vs sudden spikes, IV regime changes, theta acceleration.
- **Key moment snapshots** — full Greeks/IV/prices at peak, trough, and boundaries. Compare to sell-time context to understand what changed.
- **News around key dates** — headlines near the sell, peak, and trough dates. Identify catalysts — was a peak caused by predictable news or a surprise?
- **Market around key dates** — stock price and IV environment at those moments.
- **Counterfactual** — realized P&L vs hold-to-now, peak/trough values, missed upside, avoided downside.

Investigation questions: Was the trajectory shape predictable? Did the peak correlate with a news catalyst? Was IV expanding or contracting? Was the sell reason validated by subsequent action? Was the outcome luck or skill?

Priority on expired contracts (complete lifecycle data).

### 4. Update Experiences

Add `[hindsight]` evidence entries to relevant experience files following the rules in `experience/README.md`. Create new experiences if post-sale patterns were discovered.

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
