# Paper Trade Evaluate Skill

**Skill name**: `paper-trade-evaluate`
**Location**: `~/.openclaw/workspace/skills/paper-trade-evaluate/SKILL.md`

Eva's autonomous trading cycle — triggered by cron or on-demand. The most complex skill, involving strategy reading, data evaluation, experience recall, and trade execution.

---

## Trigger Phrases

- "run paper trading evaluation"
- "evaluate paper trades"
- "check paper positions"
- Also triggered automatically by OpenClaw cron every 15 minutes during market hours

---

## SKILL.md Content

```yaml
---
name: paper-trade-evaluate
description: >
  Autonomous paper trading evaluation cycle. Triggered by cron every 15 minutes
  during market hours, or when asked to "run paper trading evaluation",
  "evaluate paper trades", "check paper positions".
metadata:
  openclaw:
    emoji: "🤖"
    requires:
      bins: ["python3"]
---
```

## Execution Flow

### 1. Load Context

1. Read `strategy/PAPER.md` — all trading rules

Do NOT read experiences yet — form your own assessment first.

### 2. Fetch Data

```bash
python3 {baseDir}/../../options-toolkit/eva.py evaluate --all
```

Parses as a JSON array (one object per ticker from `trading_tickers.json`).

**Data guard:** Tradier sandbox data is 15 minutes delayed. Before ~9:45 AM ET, IV reads as 0% and quotes are unreliable. If `iv_context.current_avg_iv` is 0 or null, skip that ticker.

### 3. Process Recently Closed Positions

If `recently_closed` contains positions with `needs_experience_update: true`:

1. Find or create the relevant experience file in `experience/`
2. Add evidence (supporting or contradicting) with today's date and `[paper]` tag
3. Update the Analysis section if understanding has deepened
4. Update `experience/INDEX.md` if a new file was created

### 4. Make Tentative Decisions

For each ticker, apply `PAPER.md` rules to the evaluation data. Possible actions: **sell**, **buy**, **double down**, or **hold**.

Write down each tentative decision with the ticker, planned action, situation summary, and pattern tags.

### 5. Recall Experiences

Before executing, spawn an Agent (subagent_type: Explore) for each ticker where you plan to act (buy, sell, or double down — skip holds). The agent searches `experience/INDEX.md` for matching experiences by ticker and pattern tags, reads matching files, and returns findings.

Multiple recall agents can run in parallel (one per ticker).

### 6. Finalize Decisions

Review the recall agent's findings:

- **Supporting experience (medium/high confidence):** Proceed with more conviction.
- **Contradicting experience:** Reconsider — adjust or skip.
- **Disproven experience:** Do NOT repeat the same mistake.
- **No relevant experiences:** Proceed based on strategy rules alone.

### 7. Execute

Buy:
```bash
python3 {baseDir}/../../options-toolkit/eva.py buy --ticker {TICKER} --type {call|put} --strike {STRIKE} --expiry {YYYY-MM-DD} --quantity 1 --reason "{DETAILED_REASONING}"
```

Sell:
```bash
python3 {baseDir}/../../options-toolkit/eva.py sell --ticker {TICKER} --type {call|put} --strike {STRIKE} --expiry {YYYY-MM-DD} --quantity 1 --reason "{DETAILED_REASONING}"
```

`--reason` must be detailed — it feeds `reasons.json` and the experience system. Include any relevant experience findings.

### 8. Report

- **Trade action:** `buy`/`sell` commands auto-send Discord notifications.
- **Experience update:** Post a brief note about what was learned.
- **Hold (no action):** Stay silent.

---

## Guardrails

- **NEVER call `reset`.** That command is user-only.
- All strategy rules live in `PAPER.md` — this skill only defines the process.
