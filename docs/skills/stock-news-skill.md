# Stock News Skill

**Skill name**: `stock-news`
**Location**: `~/.openclaw/workspace/skills/stock-news/SKILL.md`

---

## When This Skill Is Used

This skill is **not the default for user news requests**. It is only used when headlines are being fed into a larger report or summary (e.g. the cron report's Section 4). For any direct user request about news, Eva uses `stock-news-deep` instead.

## SKILL.md Content

```yaml
---
name: stock-news
description: >
  Get recent news headlines and sentiment analysis for any stock ticker. Trigger
  when someone asks "news on X", "any headlines for X", "what's in the news
  about X", "X news", or "anything going on with X" where X is a stock ticker.
  Returns up to 8 recent headlines with sentiment scoring and key themes.
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
   python3 {baseDir}/../../options-toolkit/toolkit.py news --ticker {TICKER}
   ```
3. Post the output directly to the channel

---

## Expected Output

```
📰 LIVE NEWS HEADLINES
──────────────────────────────────────────────────────────────────────────────────────────

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

This skill provides **quick headlines** (~2s response) — post formatted text as-is. It is only used for internal/report purposes. `stock-news-deep` is the default for all user-facing news requests (~8-10s, AI-synthesized analysis).

- User asks "IWM news" → **stock-news-deep** (always)
- Cron report Section 4 → **stock-news** (internal, formatted text)
