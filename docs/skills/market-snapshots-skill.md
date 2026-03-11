# Market Snapshots Skill

**Skill name**: `market-snapshots`
**Location**: `~/.openclaw/workspace/skills/market-snapshots/SKILL.md`

---

## Trigger Phrases

The skill description should match when users say things like:
- "snapshots for AMD"
- "AMD snapshot history"
- "show me AMD peaks"
- "when was AMD IV highest"
- "AMD price peak last month"
- "market data for AMD last week"

---

## SKILL.md Content

```yaml
---
name: market-snapshots
description: >
  Query stored market snapshots for a ticker. Trigger when someone asks
  "snapshots for X", "X snapshot history", "show me X peaks", "when was X IV
  highest", "X price peak last month", or "market data for X last week" where
  X is a stock ticker.
metadata:
  openclaw:
    emoji: "📸"
    requires:
      bins: ["python3"]
---
```

### Body Instructions

Eva should:
1. Extract the ticker symbol from the user's message
2. Run the command:
   ```bash
   python3 {baseDir}/../../options-toolkit/eva.py snapshots --ticker {TICKER}
   ```
3. Summarize key findings for the user

Optional flags based on user intent:
- Date range: add `--from YYYY-MM-DD --to YYYY-MM-DD`
- Specific fields: add `--fields iv,trends` (or other field groups)
- Peaks/extremes: add `--peaks` (optionally with `--days N`)
- All intraday data: add `--all-intraday`

---

## Expected Output

JSON output. Eva summarizes key findings for the user rather than posting raw JSON.

---

## When No Data Exists

Eva should relay the error and explain: "I don't have any stored snapshot data for {TICKER} yet."

---

## Error Handling

If the command fails, Eva should say:
- "I couldn't fetch snapshots for {TICKER}."

---

## No Ticker Specified

Eva should ask: "Which ticker do you want snapshots for?"
