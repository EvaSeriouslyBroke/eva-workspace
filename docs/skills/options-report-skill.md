# Options Report Skill

**Skill name**: `options-report`
**Location**: `~/.openclaw/workspace/skills/options-report/SKILL.md`

This is the most complex skill — it produces multi-chunk output that must be split for Discord delivery.

---

## Trigger Phrases

The skill description should match when users say things like:
- "run the report for IWM"
- "full analysis on SPY"
- "send me IWM options analysis"
- "options report for QQQ"
- "what's the play on IWM?"
- "analyze AAPL options"
- "give me the breakdown on TSLA"
- "how's IWM looking?"

---

## SKILL.md Content

```yaml
---
name: options-report
description: >
  Run a facts-only options data report with IV metrics, volume, and sentiment data.
  Trigger when someone asks to "run the report", "full analysis",
  "options report", "what's the play on X", "how's X looking", "analyze X options",
  or "send me an analysis" for any stock ticker X. Produces a multi-section report
  with price, news, options chain, and IV summary.
metadata:
  openclaw:
    emoji: "🎯"
    requires:
      bins: ["python3"]
---
```

### Body Instructions

Eva should:
1. Extract the ticker symbol from the user's message
2. Run the command with `--force` (always, since this is interactive):
   ```bash
   python3 {baseDir}/../../options-toolkit/toolkit.py report --ticker {TICKER} --force
   ```
3. The output will contain `---SPLIT---` markers (~4000-5000 chars total)
4. Split the output at each `---SPLIT---` line
5. Send each chunk as a separate Discord message
6. Wait ~1 second between messages to avoid rate limits

---

## Why `--force` Is Always Passed

Interactive requests happen whenever the user asks — could be during market hours, after hours, or on weekends. The `--force` flag bypasses the market hours check so the user always gets a report. Without it, an after-hours request would produce nothing.

---

## Handling Multi-Chunk Output

The report output contains `---SPLIT---` markers at logical section boundaries:

```
[Chunk 1: Header + Price + News]
---SPLIT---
[Chunk 2: Options Tables]
---SPLIT---
[Chunk 3: IV Summary + Footer]
```

**Eva's process:**
1. Capture the entire stdout from the exec command
2. Split the text on `---SPLIT---` lines
3. For each chunk:
   a. Trim leading/trailing whitespace
   b. Send as a Discord message to the channel
   c. Wait ~1 second before sending the next chunk
4. Do NOT add any additional commentary between chunks

### Why Split?

Discord has a 2000-character message limit. Each chunk is designed to be under 1900 characters. Sending the entire report as one message would fail.

---

## Expected Output (Abbreviated)

**Chunk 1:**
```
✓ Previous data from: 2026-02-20 09:30:00 (40 minutes ago)

==========================================================================================
  🎯 IWM OPTIONS TRADING ANALYZER
==========================================================================================

Current IWM Price: $210.45 🟢 (+$0.65 / +0.31%)
Previous Close: $209.80
Analysis Time: 2026-02-20 10:10:00

📰 LIVE NEWS HEADLINES
──────────────────────────────────────────────────────────────────────────────────────────
Recent Headlines (6 articles):
  1. Fed Signals Patience on Rate Cuts
     Reuters • 2026-02-20
  ...
News Sentiment: Slightly Bullish (Score: +2)
Key Themes: Federal Reserve Policy, Small-Cap Focus
```

**Chunk 2:** Options tables (calls + puts)

**Chunk 3:** IV summary metrics + footer + save confirmation

---

## Error Handling

If the command fails (exit code 1), Eva should tell the user:
- "I couldn't generate the report for {TICKER}. The ticker might be invalid or there might be a network issue. Check if yfinance is working."

If the output is empty (no `---SPLIT---` markers), something unexpected happened. Eva should report the raw output or error.

---

## No Ticker Specified

Eva should ask: "Which ticker do you want the full analysis for?"

---

## Difference From Cron Execution

| Aspect | Interactive (this skill) | Scheduled (run_all.sh) |
|--------|--------------------------|------------------------|
| `--force` | Always passed | Never passed |
| Splitting | Eva does it | run_all.sh + awk does it |
| Delivery | Eva sends to requesting channel | run_all.sh sends to configured channel |
| Rate limiting | Eva waits ~1s between chunks | run_all.sh sleeps 1s between chunks |
| Error handling | Eva tells the user | Error goes to cron.log |
