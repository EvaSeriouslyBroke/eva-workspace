---
name: paper-trade-evaluate
description: "Autonomous paper trading evaluation cycle. Triggered by cron every 15 minutes during market hours, or when asked to 'run paper trading evaluation', 'evaluate paper trades', 'check paper positions'."
metadata:
  openclaw:
    emoji: "\U0001f916"
    requires:
      bins: ["python3"]
---

Autonomous trading evaluation cycle. Follow every step in order.

## 1. Load Context

1. Read `{baseDir}/../../strategy/PAPER.md` — all trading rules live here

Do NOT read experiences yet — form your own assessment first.

## 2. Fetch Data

```bash
python3 {baseDir}/../../options-toolkit/eva.py evaluate --all
```

Parses as a JSON array (one object per ticker).

**Data guard:** Tradier sandbox data is 15 minutes delayed. Before ~9:45 AM ET, IV reads as 0% and quotes are unreliable. If `iv_context.current_avg_iv` is 0 or null, skip that ticker.

## 3. Process Recently Closed Positions

If `recently_closed` contains positions with `needs_experience_update: true`:

1. Find or create the relevant experience file in `experience/`
2. Add evidence (supporting or contradicting) with today's date and `[paper]` tag
3. Update the Analysis section if understanding has deepened
4. Update `experience/INDEX.md` if a new file was created

## 4. Make Tentative Decisions

For each ticker, apply `PAPER.md` rules to the evaluation data. Possible actions: **sell**, **buy**, **double down**, or **hold**.

Write down each tentative decision with:
- The ticker and planned action
- The situation (price move, IV level, thesis)
- Key tags describing the pattern (e.g., mean-reversion, dip, earnings-gap, iv-spike)

## 5. Recall Experiences

Before executing, check your memory for similar past situations. Spawn an Agent (subagent_type: Explore) for each ticker where you plan to act (buy, sell, or double down — skip holds):

**Agent prompt:**
> Search Eva's trading experiences for situations similar to this:
>
> - **Ticker:** {TICKER}
> - **Planned action:** {buy call / buy put / sell / double down}
> - **Situation:** {1-2 sentence description of current conditions}
> - **Pattern tags:** {comma-separated tags}
>
> Steps:
> 1. Read `{baseDir}/../../experience/INDEX.md`
> 2. Find ALL experiences matching this ticker
> 3. Find general experiences AND experiences from other tickers with overlapping tags
> 4. Read each matching experience file
> 5. Return for each match: the file path, thesis, confidence level, key analysis points, recent evidence, and any exceptions/nuances relevant to this situation
> 6. If no experiences match, say so explicitly

You may launch multiple recall agents in parallel (one per ticker).

## 6. Finalize Decisions

Review the recall agent's findings for each ticker:

- **Supporting experience (medium/high confidence):** Proceed with more conviction. Note the experience in your reasoning.
- **Contradicting experience:** Reconsider. The thesis may need adjustment or the trade may not be worth taking.
- **Disproven experience:** Do NOT repeat the same mistake. Adjust or skip.
- **No relevant experiences:** Proceed based on strategy rules alone — this is a new pattern to learn from.

If the recall changes your decision, explain why in the `--reason`.

## 7. Execute

Buy:
```bash
python3 {baseDir}/../../options-toolkit/eva.py buy --ticker {TICKER} --type {call|put} --strike {STRIKE} --expiry {YYYY-MM-DD} --quantity 1 --reason "{DETAILED_REASONING}"
```

Sell:
```bash
python3 {baseDir}/../../options-toolkit/eva.py sell --ticker {TICKER} --type {call|put} --strike {STRIKE} --expiry {YYYY-MM-DD} --quantity 1 --reason "{DETAILED_REASONING}"
```

`--reason` must be detailed — it feeds `reasons.json` and the experience system. Include any relevant experience findings.

## 8. Report

- **Trade action:** `buy`/`sell` commands auto-send Discord notifications.
- **Experience update:** Post a brief note about what was learned.
- **Hold (no action):** Stay silent.

## Guardrails

- **NEVER call `reset`.** That command is user-only.
- All strategy rules live in `PAPER.md` — this skill only defines the process.
