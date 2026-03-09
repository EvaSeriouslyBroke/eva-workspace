# News Research Command

The `eva.py news-research` subcommand performs deep news research for a ticker — fetching full article content and web search results beyond what `eva.py news` provides.

It produces JSON output for Eva to synthesize into analysis.

---

## Usage

```
python3 eva.py news-research --ticker <SYM> [--max-articles 3] [--max-search 5] [--query "custom search"]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--ticker` | required | Ticker symbol |
| `--max-articles` | 3 | Max articles to extract full content from |
| `--max-search` | 5 | Max DuckDuckGo search results per query |
| `--query` | `"{TICKER} stock news"` | Custom search query (repeatable). Eva can pass multiple `--query` flags to search for specific topics. |

---

## What It Does

1. **Fetches yfinance news headlines** — Same as `eva.py news`, extracts article URLs and summaries
2. **Extracts full article text** — Uses `trafilatura` to download and extract content from the top N article URLs (concurrent, 15s timeout per article)
3. **Searches DuckDuckGo** — Runs each `--query` (or default `"{TICKER} stock news"`) for recent results with snippets. Multiple queries are searched independently and results combined.
4. **Runs sentiment scoring** — Same keyword-based algorithm as `eva.py news`
5. **Outputs JSON** — All data as structured JSON to stdout

---

## Pipeline Detail

### Article Extraction

- Articles are sorted to deprioritize VIDEO content types
- Top `--max-articles` are fetched concurrently via `ThreadPoolExecutor`
- Each URL is downloaded with `trafilatura.fetch_url()`, then content extracted with `trafilatura.extract()`
- Content is capped at 3000 characters per article
- If extraction fails or returns < 100 chars, falls back to DuckDuckGo `body` field
- If both fail, article is marked as `"failed"`

### Web Search

- Uses `duckduckgo-search` library (`DDGS.news()` method)
- Runs each `--query` independently (default: `"{TICKER} stock news"`)
- Returns title, URL, snippet, and source for each result
- Results from all queries are combined in `web_search` array
- Failures are captured gracefully per query (empty results + error message)

---

## Output JSON Shape

```json
{
  "ticker": "IWM",
  "timestamp": "2026-02-25T14:30:00-05:00",
  "coverage_quality": "full",
  "queries": ["IWM stock news"],
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
| `summary_fallback` | Extraction failed, used headline summary instead |
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
| `trafilatura` | Article content extraction from URLs (only imported when news-research runs) |
| `yfinance` | News headline fetching |
| `duckduckgo-search` | Web search for custom queries |

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

## Relationship to Other Subcommands

The `news-research` subcommand shares the sentiment scoring algorithm and headline fetching with `eva.py news`. The heavy dependency `trafilatura` is only imported when this subcommand runs — other subcommands are unaffected.
