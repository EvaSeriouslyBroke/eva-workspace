# News Research Command

The `news_research.py` script performs deep news research for a ticker — fetching full article content and web search results beyond what `toolkit.py news` provides.

**This is a separate script**, not a `toolkit.py` subcommand. It produces JSON output for Eva to synthesize into analysis.

---

## Usage

```
python3 news_research.py --ticker <SYM> [--max-articles 3] [--max-search 5]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--ticker` | required | Ticker symbol |
| `--max-articles` | 3 | Max articles to extract full content from |
| `--max-search` | 5 | Max DuckDuckGo search results |

---

## What It Does

1. **Fetches yfinance headlines** — Same as `toolkit.py news`, but also extracts article URLs and summaries
2. **Extracts full article text** — Uses `trafilatura` to download and extract content from the top N article URLs (concurrent, 15s timeout per article)
3. **Searches DuckDuckGo** — Queries `"{TICKER} stock news"` for recent results with snippets
4. **Runs sentiment scoring** — Same keyword-based algorithm as `toolkit.py`
5. **Outputs JSON** — All data as structured JSON to stdout

---

## Pipeline Detail

### Article Extraction

- Articles are sorted to deprioritize VIDEO content types
- Top `--max-articles` are fetched concurrently via `ThreadPoolExecutor`
- Each URL is downloaded with `trafilatura.fetch_url()`, then content extracted with `trafilatura.extract()`
- Content is capped at 3000 characters per article
- If extraction fails or returns < 100 chars, falls back to yfinance `summary` field
- If both fail, article is marked as `"failed"`

### Web Search

- Uses `duckduckgo-search` library (`DDGS.news()` method)
- Query: `"{TICKER} stock news"`
- Returns title, URL, snippet, and source for each result
- Failures are captured gracefully (empty results + error message)

---

## Output JSON Shape

```json
{
  "ticker": "IWM",
  "timestamp": "2026-02-25T14:30:00-05:00",
  "coverage_quality": "full",
  "headlines": [
    {
      "title": "Fed Signals Patience...",
      "publisher": "Reuters",
      "date": "2026-02-25",
      "url": "https://..."
    }
  ],
  "deep_articles": [
    {
      "title": "Fed Signals Patience...",
      "publisher": "Reuters",
      "date": "2026-02-25",
      "url": "https://...",
      "content": "Full article text up to 3000 chars...",
      "extraction_method": "trafilatura"
    }
  ],
  "web_search": [
    {
      "title": "IWM rallies on earnings...",
      "url": "https://...",
      "snippet": "The Russell 2000 ETF...",
      "source": "MarketWatch"
    }
  ],
  "sentiment": {
    "label": "Slightly Bullish",
    "score": 2
  },
  "themes": ["Federal Reserve Policy", "Small-Cap Focus"],
  "errors": ["Article extraction failed for Bloomberg (paywall)"]
}
```

### `extraction_method` Values

| Value | Meaning |
|-------|---------|
| `trafilatura` | Full content successfully extracted |
| `summary_fallback` | Extraction failed, used yfinance summary instead |
| `failed` | No content available |

### `coverage_quality` Values

| Value | Condition |
|-------|-----------|
| `full` | All `deep_articles` have `extraction_method: "trafilatura"` |
| `partial` | At least one article fell back to `summary_fallback` or `failed` |
| `headlines_only` | Zero articles have extracted content (all failed/empty) |

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `trafilatura` | Article content extraction from URLs |
| `duckduckgo-search` | Web search without API keys |
| `yfinance` | Headline fetching (shared with toolkit.py) |

These are only imported by `news_research.py` — `toolkit.py` and cron are unaffected.

---

## Error Cases

| Scenario | Behavior |
|----------|----------|
| No headlines from yfinance | stderr message, exit 1 |
| Paywalled article | Falls back to summary, logs in `errors` array |
| trafilatura timeout | Falls back to summary, logs in `errors` array |
| DuckDuckGo rate limited | Empty `web_search`, error logged |
| Network failure | stderr message, exit 1 |
| All extractions fail | `coverage_quality: "headlines_only"`, Eva works from headlines + search |

---

## Relationship to toolkit.py

`news_research.py` is a **separate standalone script**, not a toolkit.py subcommand. This keeps the existing toolkit and cron pipeline completely untouched. The only shared element is the sentiment scoring algorithm (duplicated, not imported, to keep scripts independent).
