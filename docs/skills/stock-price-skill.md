# Stock Price Skill

**Skill name**: `stock-price`
**Location**: `~/.openclaw/workspace/skills/stock-price/SKILL.md`

---

## Trigger Phrases

The skill description should match when users say things like:
- "what's IWM at?"
- "price of SPY"
- "how's AAPL doing?"
- "check TSLA price"
- "QQQ quote"
- "where's IWM trading?"

---

## SKILL.md Content

```yaml
---
name: stock-price
description: >
  Check current stock prices and daily changes. Trigger when someone asks
  "what's X at", "price of X", "how's X doing", "check X price", or "X quote"
  where X is any stock ticker symbol.
metadata:
  openclaw:
    emoji: "💲"
    requires:
      bins: ["python3"]
---
```

### Body Instructions

Eva should:
1. Extract the ticker symbol from the user's message
2. Run the command:
   ```bash
   python3 {baseDir}/../../options-toolkit/eva.py price --ticker {TICKER}
   ```
3. Post the output directly to the channel — no additional formatting needed

---

## Expected Output

```
Current IWM Price: $210.45 🟢 (+$0.65 / +0.31%)
Previous Close: $209.80
Analysis Time: 2026-02-20 10:30:00
```

Short, clean, 3 lines. Eva posts this as-is.

---

## Error Handling

If the command fails (exit code 1), Eva should tell the user:
- "I couldn't fetch the price for {TICKER}. The ticker might be invalid or there might be a network issue."

---

## No Ticker Specified

If the user says something like "check the price" without a ticker, Eva should ask:
- "Which ticker do you want me to check?"
