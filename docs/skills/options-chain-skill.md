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
   python3 {baseDir}/../../options-toolkit/eva.py chain --ticker {TICKER}
   ```
3. Post the output directly to the channel

---

## Expected Output

The output uses stacked 3-line cards inside code blocks (10 strikes, showing abbreviated example with 3):

```
Target Expiration: 2026-05-16 (85 days)
ATM Strike: $210
```
```
📈 CALLS
```
~~~
```
$212 OTM | IV: 24.50%
  Chg: N/A | B/A: $3.20/$3.45
  Last: $3.30 | Vol: 1,245 | OI: 8,901

$210 ATM | IV: 23.20%
  Chg: N/A | B/A: $4.50/$4.75
  Last: $4.60 | Vol: 3,456 | OI: 15,678

$208 ITM | IV: 22.50%
  Chg: N/A | B/A: $5.90/$6.15
  Last: $6.00 | Vol: 987 | OI: 7,654
```
~~~
```
📉 PUTS
```
(same card format, with reversed ITM/OTM status)

Standalone `chain` always shows `N/A` for IV change (no history loaded). The `report` command populates actual change values.

Eva posts the output as-is. Single Discord message.

---

## Error Handling

If the command fails (exit code 1), Eva should tell the user:
- "I couldn't fetch the options chain for {TICKER}. The ticker might not have options available, or there might be a network issue."

---

## No Ticker Specified

If the user says "show me the chain" without a ticker, Eva should ask:
- "Which ticker do you want the options chain for?"
