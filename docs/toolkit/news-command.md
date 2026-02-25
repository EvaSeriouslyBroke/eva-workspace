# News Command

The `news` subcommand fetches recent headlines for a ticker and provides sentiment analysis.

---

## Usage

```
python3 toolkit.py news --ticker <SYM> [--json]
```

---

## What It Fetches

```python
import yfinance as yf
ticker = yf.Ticker(sym)
articles = ticker.news  # List of dicts
```

### Fields Extracted Per Article

| Field | Source | Description |
|-------|--------|-------------|
| Title | `article['title']` | Headline text |
| Publisher | `article['publisher']` | Source name (Reuters, CNBC, etc.) |
| Date | `article['providerPublishTime']` | Unix timestamp → formatted date |
| URL | `article['content']['clickThroughUrl']` or `article['link']` | Article link (used by `news_research.py`, ignored by `format_news()`) |
| Summary | `article['content']['summary']` or `article['summary']` | Brief summary text (used by `news_research.py` as fallback) |
| Content Type | `article['content']['contentType']` or `article['type']` | e.g. "STORY", "VIDEO" (used by `news_research.py` to deprioritize video) |

### URL Extraction

The `fetch_news()` function extracts article URLs from yfinance data. For `content`-style responses, URLs come from `clickThroughUrl` (dict with `url` key, or bare string) with `canonicalUrl` as fallback. For responses without a `content` dict, URLs come from the `link` field.

These extra fields (`url`, `summary`, `content_type`) are included in the parsed dict but **ignored by `format_news()`** — the formatted text output is unchanged. They are used by `news_research.py` for deep article extraction.

### Limits

- Display up to **8 headlines** (the most recent ones)
- If yfinance returns fewer than 8, show all available
- If yfinance returns 0, show warning: `⚠️  No news headlines available`

---

## Headline Truncation

Any headline longer than 85 characters is truncated and appended with `...`:

```
Original:  "Federal Reserve Chairman Signals Potential Rate Adjustments Could Be Coming In The Next Quarter"
Truncated: "Federal Reserve Chairman Signals Potential Rate Adjustments Could Be Coming In The N..."
```

Rule: If `len(headline) > 85`, display `headline[:85] + "..."`

---

## Formatted Output

Matches Section 4 of OUTPUT.md:

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

### Indentation

- Headline number and text: 2-space indent
- Publisher and date line: 5-space indent
- Warning lines: 2-space indent

---

## Sentiment Scoring Algorithm

### Step 1: Score Each Headline

Each headline is scored by keyword matching. The score for all headlines is summed.

**Bullish keywords** (each occurrence adds +1):
- rally, surge, gain, rise, bull, up, high, record, strong, growth, beat, exceed, optimistic, soar, breakout, rebound, recovery, positive, boost, momentum

**Bearish keywords** (each occurrence adds -1):
- fall, drop, decline, bear, down, low, crash, weak, miss, fear, sell, plunge, slump, recession, negative, concern, warning, risk, loss, cut

Words are matched case-insensitively as substrings of the headline.

### Step 2: Map Total Score to Label

| Score Range | Label |
|-------------|-------|
| > +3 | Bullish |
| +1 to +3 | Slightly Bullish |
| 0 | Neutral |
| -1 to -3 | Slightly Bearish |
| < -3 | Bearish |

### Step 3: Display

```
News Sentiment: {Label} (Score: {+/-N})
```

---

## Key Themes Detection

Scan all headlines for theme keywords and list detected themes:

| Theme | Detection Keywords |
|-------|-------------------|
| Federal Reserve Policy | fed, federal reserve, rate, monetary, powell, fomc, interest rate |
| Trade/Tariffs | tariff, trade war, trade deal, import, export, duties, trade tensions |
| Small-Cap Focus | small-cap, small cap, russell, iwm, small-caps |
| General Market News | market, s&p, nasdaq, dow, stocks, equities, wall street |

Themes are listed in the order shown above. Only include themes where at least one keyword matched.

---

## Conditional Warning Lines

These lines appear ONLY when their condition is met:

```
  ⚠️  High Fed/monetary policy focus in recent news        ← only if ≥2 headlines match Fed keywords
  ⚠️  High tariff/trade focus in recent news               ← only if ≥2 headlines match tariff keywords
```

---

## JSON Mode Output

```json
{
  "ticker": "IWM",
  "headline_count": 6,
  "headlines": [
    {
      "title": "Fed Signals Patience on Rate Cuts Amid Inflation Concerns",
      "publisher": "Reuters",
      "date": "2026-02-20",
      "url": "https://finance.yahoo.com/news/...",
      "summary": "Federal Reserve officials...",
      "content_type": "STORY",
      "score": -1
    }
  ],
  "sentiment": {
    "label": "Slightly Bullish",
    "score": 2
  },
  "themes": ["Federal Reserve Policy", "Small-Cap Focus"],
  "warnings": {
    "high_fed_focus": true,
    "high_tariff_focus": false
  }
}
```

---

## Error Cases

| Scenario | Behavior |
|----------|----------|
| No news available | Shows `⚠️  No news headlines available`, sentiment = Neutral (0) |
| Invalid ticker | stderr message, exit 1 |
| Network failure | stderr message, exit 1 |
| Headline missing publisher | Shows "Unknown" as publisher |
| Headline missing date | Shows "N/A" as date |
