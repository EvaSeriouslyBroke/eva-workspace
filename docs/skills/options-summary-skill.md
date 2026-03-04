# Options Summary Skill

**Skill name**: `options-summary`
**Location**: `~/.openclaw/workspace/skills/options-summary/SKILL.md`

Provides an interactive end-of-day summary with technical and market analysis.

---

## Trigger Phrases

The skill description should match when users say things like:
- "summary of today for IWM"
- "how did IWM do today?"
- "end of day summary"
- "daily recap for SPY"
- "today's recap on QQQ"
- "wrap up on IWM"
- "what happened with IWM today?"
- "day summary for AAPL"

---

## SKILL.md Content

```yaml
---
name: options-summary
description: >
  Run an end-of-day summary with intraday analysis of IV, volume, skew, OI,
  and price movements. Trigger when someone asks for a "summary of today",
  "end of day summary", "how did X do today", "daily recap", "today's recap",
  "day summary for X", "wrap up on X", or "what happened with X today"
  for any stock ticker X.
metadata:
  openclaw:
    emoji: "📊"
    requires:
      bins: ["python3"]
---
```

### Body Instructions

Eva should:
1. Extract the ticker symbol from the user's message
2. Run the command with `--force` (always, since this is interactive):
   ```bash
   python3 {baseDir}/../../options-toolkit/toolkit.py summary --ticker {TICKER} --force
   ```
3. The output will contain `---SPLIT---` markers (3 chunks)
4. Split the output at each `---SPLIT---` line
5. Send each chunk as a separate Discord message
6. Wait ~1 second between messages to avoid rate limits

---

## Why `--force` Is Always Passed

Interactive requests happen whenever the user asks. The `--force` flag bypasses the schedule check (normally 4:01 PM only) so the user gets a summary on demand.

---

## Handling Multi-Chunk Output

```
[Chunk 1: Header + Price Action]
---SPLIT---
[Chunk 2: Intraday Metrics (IV, Volume, OI, Skew)]
---SPLIT---
[Chunk 3: Technical Analysis + Market Assessment + Day Rating]
```

Same splitting process as the options-report skill.

---

## Empty Output

The summary requires at least 2 snapshots with valid IV (>= 1%) from today. If the user asks before enough data exists (e.g., before 11:00 AM), the output will be empty. Eva should explain that not enough data is available yet.

---

## Error Handling

If the command fails (exit code 1), Eva should tell the user:
- "I couldn't generate the summary for {TICKER}. The ticker might be invalid or there might be a network issue."

---

## No Ticker Specified

Eva should ask: "Which ticker do you want the end-of-day summary for?"

---

## Difference From Scheduled Execution

| Aspect | Interactive (this skill) | Scheduled (cron) |
|--------|--------------------------|------------------------|
| `--force` | Always passed | Never passed |
| Timing | Anytime user asks | 4:01 PM ET only |
| Splitting | Eva does it | run_all.sh + awk does it |
| Delivery | Eva sends to requesting channel | run_all.sh sends to configured channel |
| Empty output | Eva explains why | Silent skip |
