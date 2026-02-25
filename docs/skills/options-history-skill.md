# Options History Skill

**Skill name**: `options-history`
**Location**: `~/.openclaw/workspace/skills/options-history/SKILL.md`

---

## Trigger Phrases

The skill description should match when users say things like:
- "IV history for IWM"
- "how has SPY IV been trending?"
- "previous runs for IWM"
- "IWM history"
- "what was IV on IWM yesterday?"
- "show me the trend for QQQ"
- "IV tracking for AAPL"

---

## SKILL.md Content

```yaml
---
name: options-history
description: >
  Show recent IV history and trends from stored data. Trigger when someone asks
  "IV history for X", "how has X IV been trending", "previous runs for X",
  "X history", "what was IV on X yesterday", or "X trend" where X is a stock
  ticker. Returns a table of recent trading days with IV, price, and ratio data.
metadata:
  openclaw:
    emoji: "📅"
    requires:
      bins: ["python3"]
---
```

### Body Instructions

Eva should:
1. Extract the ticker symbol from the user's message
2. Run the command:
   ```bash
   python3 {baseDir}/../../options-toolkit/toolkit.py history --ticker {TICKER}
   ```
3. Post the output directly to the channel

If the user mentions a specific number of days (e.g., "last 10 days"), add `--days N`:
   ```bash
   python3 {baseDir}/../../options-toolkit/toolkit.py history --ticker {TICKER} --days 10
   ```

---

## Expected Output

```
📊 IV HISTORY - IWM (Last 5 Trading Days)
──────────────────────────────────────────────────────────────────────────────────────────

Date          Price      Avg IV     Call IV    Put IV     P/C Vol    P/C OI     Skew
2026-02-20    $210.45    25.30%     24.50%     26.10%     1.05       0.92       +1.60%
2026-02-19    $209.80    25.10%     24.20%     26.00%     1.12       0.95       +1.80%
2026-02-18    $211.20    24.80%     23.90%     25.70%     0.98       0.88       +1.80%
2026-02-17    $210.90    25.50%     24.80%     26.20%     1.08       0.91       +1.40%
2026-02-14    $209.50    26.10%     25.30%     26.90%     1.15       0.97       +1.60%

Trend: IV ↓ CONTRACTING (-0.80% over 5 days)
```

Eva posts this as-is. Single Discord message.

---

## When No History Exists

The command will output: `No history data found for {TICKER}`

Eva should relay this and explain: "I don't have any stored data for {TICKER} yet. Run a report first to start tracking IV history."

---

## Error Handling

If the command fails, Eva should say:
- "I couldn't fetch history for {TICKER}."

---

## No Ticker Specified

Eva should ask: "Which ticker do you want the IV history for?"
