# Stock News Skill

**Skill name**: `stock-news`
**Location**: `~/.openclaw/workspace/skills/stock-news/SKILL.md`

---

## When This Skill Is Used

This skill is **not the default for user news requests**. It is only used when Eva needs a fast, formatted news snippet (e.g., composing a multi-part response). For any direct user request about news, Eva uses `stock-news-deep` instead.

## SKILL.md Content

```yaml
---
name: stock-news
description: >
  Quick headline summary for a stock ticker — no deep analysis. ONLY use this when
  you need a fast, formatted news snippet (e.g. composing a multi-part response).
  For any direct user request about news — including "X news", "news on X",
  "what's going on with X" — use the stock-news-deep skill instead, which provides
  real analysis.
metadata:
  openclaw:
    emoji: "📰"
    requires:
      bins: ["python3"]
---
```

### Body Instructions

Eva should:
1. Extract the ticker symbol from the user's message
2. Run the command:
   ```bash
   python3 {baseDir}/../../options-toolkit/eva.py news --ticker {TICKER}
   ```
3. Post the output directly to the channel

---

## Expected Output

```
📰 LIVE NEWS HEADLINES
────────────────────────────────────────

Recent Headlines (6 articles):
  1. Fed Signals Patience on Rate Cuts Amid Inflation Concerns
     Reuters • 2026-02-20
  2. Small-Cap Stocks Rally on Strong Earnings Reports
     CNBC • 2026-02-20
  3. Trade Tensions Rise as New Tariff Proposals Surface
     Bloomberg • 2026-02-19
  4. IWM ETF Sees Record Inflows as Investors Bet on Small Caps
     MarketWatch • 2026-02-19
  5. Market Volatility Increases Ahead of Economic Data Release
     Yahoo Finance • 2026-02-18
  6. Russell 2000 Companies Report Mixed Q4 Earnings
     Barron's • 2026-02-18

News Sentiment: Slightly Bullish (Score: +2)
Key Themes: Federal Reserve Policy, Small-Cap Focus
  ⚠️  High Fed/monetary policy focus in recent news
```

Eva posts this as-is. Single Discord message.

---

## Error Handling

If the command fails, Eva should say:
- "I couldn't fetch news for {TICKER}. There might be a network issue."

---

## No Ticker Specified

Eva should ask: "Which ticker do you want news for?"

---

## Distinction from stock-news-deep

This skill provides **quick headlines** (~2s response) — post formatted text as-is. It is only used when Eva needs a fast formatted snippet. `stock-news-deep` is the default for all user-facing news requests (~8-10s, AI-synthesized analysis).

- User asks "IWM news" → **stock-news-deep** (always)
- Eva composing a multi-part response → **stock-news** (fast, formatted text)
