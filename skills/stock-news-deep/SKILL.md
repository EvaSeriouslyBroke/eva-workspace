---
name: stock-news-deep
description: "Run a Python script that analyzes news for a stock ticker. The script handles everything — you just run it and read the JSON output. No browser or web search tools needed. This is the DEFAULT news skill for any user-facing news request. Trigger when someone asks about news for a ticker: 'X news', 'news on X', 'what's going on with X', 'anything happening with X', 'summarize the recent X news', 'trump tariff news for X', 'dig into X news', 'research X news', 'what's really going on with X', or any request about a specific news topic related to a ticker."
metadata:
  openclaw:
    emoji: "🔬"
    requires:
      bins: ["python3"]
---

Extract the ticker symbol from the user's message. Then run this command — it is a self-contained Python script that does all data fetching internally (you do NOT need browser access, web search tools, or any other capabilities beyond `exec`):

```bash
python3 {baseDir}/../../options-toolkit/news_research.py --ticker {TICKER}
```

The script outputs JSON to stdout. Key fields in the JSON:
- `coverage_quality`: "full", "partial", or "headlines_only"
- `deep_articles`: Array of articles with extracted `content` (up to 3000 chars each)
- `web_search`: Array of additional news results with snippets
- `headlines`: All headlines
- `sentiment`: Keyword-based sentiment label and score
- `themes`: Detected themes (Fed policy, tariffs, small-cap, etc.)
- `errors`: Any extraction failures

## How to Respond

**Read the JSON, then write your own analysis.** Do NOT relay the raw JSON or list headlines with numbers. Synthesize everything into flowing prose.

### Content Balance

- **90% news substance** — What happened? Why does it matter? Key details and quotes from the articles. How different sources are covering it. What's developing or unresolved.
- **10% market impact** — One brief paragraph connecting the news to the ticker's price action or options positioning.

### Coverage Quality Check

Before writing, check `coverage_quality` and `errors`:

- **`"full"`** — You have full article content. Proceed with deep analysis. No disclaimer needed.
- **`"partial"`** — Some articles couldn't be fully extracted. Lead with a one-line note, e.g.: *"Heads up — I couldn't pull the full article from Bloomberg (likely paywalled), so this is based on the Reuters piece and web search results."* Then proceed with analysis using what you have.
- **`"headlines_only"`** — All article extractions failed. Be honest: *"I couldn't extract article content for {TICKER} — hitting paywalls across the board. Here's what I can piece together from the headlines and web search:"* Then do your best with headlines + web search snippets.
- If `web_search` is also empty, note that too and work from headlines alone.

**Never pretend to have read content you didn't. Never silently degrade.**

### Format

- 1-3 Discord messages, each under 1900 characters
- If multiple messages needed, use `---SPLIT---` between them
- Flowing prose with **bold** for emphasis — not bullet dumps
- No raw JSON, no numbered headline lists, no generic market commentary
- Use specific details from the articles (names, numbers, quotes when available)

### Error Handling

If the command fails (exit code 1), tell the user:
"I couldn't research news for {TICKER}. There might be a network issue."

If no ticker is specified, ask: "Which ticker do you want me to dig into?"
