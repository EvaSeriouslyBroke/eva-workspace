# Options Chain Skill

**Skill name**: `options-chain`
**Location**: `~/.openclaw/workspace/skills/options-chain/SKILL.md`

---

## Trigger Phrases

The skill description should match when users say things like:
- "options chain for IWM"
- "show me SPY calls and puts"
- "what are IWM options looking like?"
- "IWM chain"
- "QQQ strikes"
- "what's the chain on AAPL?"
- "show me the options"

---

## SKILL.md Content

```yaml
---
name: options-chain
description: >
  Show options chain data with implied volatility for any ticker. Trigger when
  someone asks for "options chain", "calls and puts", "options for X", "X chain",
  "X strikes", or "what are X options looking like" where X is a stock ticker.
  Returns call and put tables with IV, bid/ask, volume, and open interest for
  5 strikes near the money.
metadata:
  openclaw:
    emoji: "⛓️"
    requires:
      bins: ["python3"]
---
```

### Body Instructions

Eva should:
1. Extract the ticker symbol from the user's message
2. Run the command:
   ```bash
   python3 {baseDir}/../../options-toolkit/toolkit.py chain --ticker {TICKER}
   ```
3. Post the output directly to the channel

---

## Expected Output

```
Target Expiration: 2026-05-16 (85 days)
ATM Strike: $210

📈 CALL OPTIONS - Implied Volatility
──────────────────────────────────────────────────────────────────────────────────────────

Strike       IV           IV Chg       Bid        Ask        Last       Vol        OI           Status
$212        🟡 24.50%     N/A 🟡      $3.20      $3.45      $3.30      1,245      8,901        OTM 🔵
$211        🟡 23.80%     N/A 🟡      $3.85      $4.10      $3.95      2,100      12,345       OTM 🔵
$210        🟡 23.20%     N/A 🟡      $4.50      $4.75      $4.60      3,456      15,678       ATM 🟡
$209        🟡 22.90%     N/A 🟡      $5.20      $5.45      $5.30      1,890      10,234       ITM 🟢
$208        🟡 22.50%     N/A 🟡      $5.90      $6.15      $6.00      987        7,654        ITM 🟢

📉 PUT OPTIONS - Implied Volatility
──────────────────────────────────────────────────────────────────────────────────────────

Strike       IV           IV Chg       Bid        Ask        Last       Vol        OI           Status
$212        🟡 26.80%     N/A 🟡      $5.10      $5.35      $5.20      890        6,543        ITM 🟢
$211        🟡 26.20%     N/A 🟡      $4.40      $4.65      $4.50      1,200      8,901        ITM 🟢
$210        🟡 25.80%     N/A 🟡      $3.80      $4.05      $3.90      2,890      13,456       ATM 🟡
$209        🟡 25.30%     N/A 🟡      $3.20      $3.45      $3.30      1,567      9,876        OTM 🔵
$208        🟡 24.80%     N/A 🟡      $2.70      $2.95      $2.80      734        5,432        OTM 🔵
```

This output is longer but still fits in one Discord message (~1500 chars). Eva posts it as-is.

---

## Error Handling

If the command fails (exit code 1), Eva should tell the user:
- "I couldn't fetch the options chain for {TICKER}. The ticker might not have options available, or there might be a network issue."

---

## No Ticker Specified

If the user says "show me the chain" without a ticker, Eva should ask:
- "Which ticker do you want the options chain for?"
