# Stock News Deep Skill

**Skill name**: `stock-news-deep`
**Location**: `~/.openclaw/workspace/skills/stock-news-deep/SKILL.md`

---

## Trigger Phrases

This is the **default skill for all user-facing news requests**. It matches:
- "IWM news", "news on SPY"
- "what's going on with AAPL?"
- "anything happening with QQQ?"
- "summarize the recent tariff news for IWM"
- "dig into IWM news", "research IWM news"
- "what's really going on with QQQ?"
- "break down TSLA news"
- Any request about a specific news topic related to a ticker (e.g. "trump tariffs and IWM")

---

## SKILL.md Content

```yaml
---
name: stock-news-deep
description: >
  Run a Python script that analyzes news for a stock ticker. The script handles
  everything — you just run it and read the JSON output. No browser or web
  search tools needed. This is the DEFAULT news skill for any user-facing news
  request. Trigger when someone asks about news for a ticker: "X news",
  "news on X", "what's going on with X", "summarize the recent X news",
  "dig into X news", "research X news", or any request about a specific news
  topic related to a ticker.
metadata:
  openclaw:
    emoji: "🔬"
    requires:
      bins: ["python3"]
---
```

### Body Instructions

Eva should:
1. Extract the ticker symbol from the user's message
2. Run `python3 {baseDir}/../../options-toolkit/news_research.py --ticker {TICKER}`
3. Read the JSON output
4. Check `coverage_quality` and be transparent about data gaps
5. Write a synthesized analysis (90% news substance, 10% market impact)
6. Format as 1-3 Discord messages (<1900 chars each), use `---SPLIT---` if multiple

---

## Key Behavior: AI Synthesis, Not Data Relay

Unlike `stock-news` (which posts toolkit output as-is), this skill requires Eva to **read the data and write her own analysis**. No raw JSON, no numbered headline lists.

### Coverage Quality Transparency

Eva checks the `coverage_quality` field:
- `"full"` — No disclaimer needed. Full analysis.
- `"partial"` — One-line note about what couldn't be read, then proceed.
- `"headlines_only"` — Honest disclaimer, then best-effort from headlines + web search.

Eva never pretends to have read content she didn't access.

---

## Expected Output Style

Flowing prose with bold emphasis. Example:

> **Small caps are catching a bid this week**, driven primarily by better-than-expected earnings from Russell 2000 components. According to Reuters, the IWM ETF saw its highest weekly inflows since November...
>
> The Bloomberg piece focuses on a different angle — **tariff uncertainty is disproportionately hitting small-cap importers**, particularly in the consumer discretionary space...
>
> From a market perspective, this push-pull dynamic explains the elevated IV we've been seeing. The options market is pricing in a wider range of outcomes than usual.

---

## Distinction from stock-news

| Aspect | stock-news | stock-news-deep |
|--------|-----------|----------------|
| When used | Internal/report only (cron Section 4) | **All user-facing news requests** |
| Speed | ~2 seconds | ~8-10 seconds |
| Data source | yfinance headlines only | yfinance + full articles + web search |
| Output | Formatted text (post as-is) | JSON → Eva synthesizes |
| Eva's role | Relay | Analyze and write |
| Depth | Headlines + sentiment | Full article content + cross-source synthesis |

---

## Error Handling

If the command fails, Eva should say:
- "I couldn't research news for {TICKER}. There might be a network issue."

---

## No Ticker Specified

Eva should ask: "Which ticker do you want me to dig into?"
