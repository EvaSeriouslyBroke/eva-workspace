#!/usr/bin/env python3
"""Deep News Research — Fetches full article content and web search results for a ticker."""

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from zoneinfo import ZoneInfo

import yfinance as yf

ET = ZoneInfo("America/New_York")

# ── Sentiment (same logic as toolkit.py) ────────────────────────────────────

BULLISH_KEYWORDS = [
    "rally", "surge", "gain", "rise", "bull", "up", "high", "record",
    "strong", "growth", "beat", "exceed", "optimistic", "soar", "breakout",
    "rebound", "recovery", "positive", "boost", "momentum",
]
BEARISH_KEYWORDS = [
    "fall", "drop", "decline", "bear", "down", "low", "crash", "weak",
    "miss", "fear", "sell", "plunge", "slump", "recession", "negative",
    "concern", "warning", "risk", "loss", "cut",
]
THEME_MAP = {
    "Federal Reserve Policy": ["fed", "federal reserve", "rate", "monetary", "powell", "fomc", "interest rate"],
    "Trade/Tariffs": ["tariff", "trade war", "trade deal", "import", "export", "duties", "trade tensions"],
    "Small-Cap Focus": ["small-cap", "small cap", "russell", "iwm", "small-caps"],
    "General Market News": ["market", "s&p", "nasdaq", "dow", "stocks", "equities", "wall street"],
}


def score_sentiment(articles):
    total = 0
    for a in articles:
        title = a.get("title", "").lower()
        for kw in BULLISH_KEYWORDS:
            if kw in title:
                total += 1
        for kw in BEARISH_KEYWORDS:
            if kw in title:
                total -= 1

    if total > 3:
        label = "Bullish"
    elif total >= 1:
        label = "Slightly Bullish"
    elif total == 0:
        label = "Neutral"
    elif total >= -3:
        label = "Slightly Bearish"
    else:
        label = "Bearish"

    themes = []
    all_text = " ".join(a.get("title", "") for a in articles).lower()
    for theme, keywords in THEME_MAP.items():
        if any(kw in all_text for kw in keywords):
            themes.append(theme)
    if not themes:
        themes = ["General Market News"]

    return {"label": label, "score": total}, themes


# ── yfinance headline fetching ──────────────────────────────────────────────

def fetch_headlines(sym):
    """Fetch headlines from yfinance, extracting URLs and summaries."""
    ticker = yf.Ticker(sym)
    articles = ticker.news or []
    parsed = []
    for a in articles[:8]:
        url = ""
        summary = ""
        content_type = ""
        if "content" in a and isinstance(a["content"], dict):
            c = a["content"]
            title = c.get("title", a.get("title", ""))
            publisher = (c.get("provider", {}).get("displayName", "Unknown")
                         if isinstance(c.get("provider"), dict) else "Unknown")
            pub_time = c.get("pubDate", "")
            ctu = c.get("clickThroughUrl")
            if isinstance(ctu, dict):
                url = ctu.get("url", "")
            elif isinstance(ctu, str):
                url = ctu
            if not url:
                canon = c.get("canonicalUrl")
                if isinstance(canon, dict):
                    url = canon.get("url", "")
            summary = c.get("summary", "")
            content_type = c.get("contentType", "")
            try:
                dt = datetime.fromisoformat(pub_time.replace("Z", "+00:00")) if pub_time else None
                date_str = dt.strftime("%Y-%m-%d") if dt else "N/A"
            except (ValueError, AttributeError):
                date_str = "N/A"
        else:
            title = a.get("title", "")
            publisher = a.get("publisher", "Unknown")
            pub_time = a.get("providerPublishTime", 0)
            url = a.get("link", "")
            summary = a.get("summary", "")
            content_type = a.get("type", "")
            if isinstance(pub_time, (int, float)) and pub_time > 0:
                date_str = datetime.fromtimestamp(pub_time, tz=ET).strftime("%Y-%m-%d")
            else:
                date_str = "N/A"
        parsed.append({
            "title": title,
            "publisher": publisher,
            "date": date_str,
            "url": url,
            "summary": summary,
            "content_type": content_type,
        })
    return parsed


# ── Article content extraction ──────────────────────────────────────────────

def extract_article(article, max_content=3000):
    """Extract full article content using trafilatura. Returns enriched article dict."""
    url = article.get("url", "")
    result = {
        "title": article["title"],
        "publisher": article["publisher"],
        "date": article["date"],
        "url": url,
        "content": "",
        "extraction_method": "failed",
    }

    if not url:
        result["content"] = article.get("summary", "")[:max_content]
        if result["content"]:
            result["extraction_method"] = "summary_fallback"
        return result, None

    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_comments=False,
                                       include_tables=False, favor_recall=True)
            if text and len(text.strip()) > 100:
                cleaned = text.strip()
                # Detect paywall/subscription gates
                paywall_phrases = [
                    "subscription plan is required",
                    "upgrade to read",
                    "subscribe to continue",
                    "sign in to read",
                    "premium content",
                    "this content is for subscribers",
                ]
                is_paywall = any(p in cleaned.lower() for p in paywall_phrases)
                if is_paywall and len(cleaned) < 500:
                    # Short content with paywall markers — treat as paywalled
                    fallback = article.get("summary", "")[:max_content]
                    if fallback:
                        result["content"] = fallback
                        result["extraction_method"] = "summary_fallback"
                        return result, f"Article extraction failed for {article['publisher']} (paywall)"
                    result["content"] = cleaned[:max_content]
                    result["extraction_method"] = "summary_fallback"
                    return result, f"Article extraction failed for {article['publisher']} (paywall, no summary available)"
                result["content"] = cleaned[:max_content]
                result["extraction_method"] = "trafilatura"
                return result, None
    except Exception as e:
        error_msg = f"Article extraction failed for {article['publisher']} ({e})"
        # Fall through to summary fallback
        result["content"] = article.get("summary", "")[:max_content]
        if result["content"]:
            result["extraction_method"] = "summary_fallback"
        return result, error_msg

    # trafilatura returned empty — try summary fallback
    fallback = article.get("summary", "")[:max_content]
    if fallback:
        result["content"] = fallback
        result["extraction_method"] = "summary_fallback"
        return result, f"Article extraction failed for {article['publisher']} (empty content, used summary)"
    return result, f"Article extraction failed for {article['publisher']} (no content available)"


def extract_articles_concurrent(articles, max_articles=3, max_content=3000):
    """Extract content from top articles concurrently."""
    # Deprioritize VIDEO content
    prioritized = sorted(articles, key=lambda a: 1 if "video" in a.get("content_type", "").lower() else 0)
    targets = prioritized[:max_articles]

    results = []
    errors = []

    with ThreadPoolExecutor(max_workers=max_articles) as executor:
        future_map = {
            executor.submit(extract_article, a, max_content): a
            for a in targets
        }
        for future in as_completed(future_map, timeout=45):
            try:
                result, error = future.result(timeout=15)
                results.append(result)
                if error:
                    errors.append(error)
            except Exception as e:
                a = future_map[future]
                results.append({
                    "title": a["title"],
                    "publisher": a["publisher"],
                    "date": a["date"],
                    "url": a.get("url", ""),
                    "content": "",
                    "extraction_method": "failed",
                })
                errors.append(f"Article extraction failed for {a['publisher']} ({e})")

    return results, errors


# ── Web search ──────────────────────────────────────────────────────────────

def search_web(ticker, max_results=5):
    """Search DuckDuckGo for recent news about the ticker."""
    try:
        import warnings
        warnings.filterwarnings("ignore", message=".*has been renamed.*")
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.news(f"{ticker} stock news", max_results=max_results))
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("body", ""),
                "source": r.get("source", ""),
            }
            for r in results
        ], None
    except Exception as e:
        return [], f"Web search failed: {e}"


# ── Main ────────────────────────────────────────────────────────────────────

def research(ticker, max_articles=3, max_search=5):
    """Run full deep news research for a ticker. Returns dict."""
    errors = []

    # 1. Fetch headlines from yfinance
    try:
        headlines = fetch_headlines(ticker)
    except Exception as e:
        print(f"Error fetching headlines for {ticker}: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Extract full article content (concurrent)
    deep_articles, extraction_errors = extract_articles_concurrent(
        headlines, max_articles=max_articles
    )
    errors.extend(extraction_errors)

    # 3. Web search
    web_results, search_error = search_web(ticker, max_results=max_search)
    if search_error:
        errors.append(search_error)

    # 4. Sentiment scoring (use all headlines)
    sentiment, themes = score_sentiment(headlines)

    # 5. Coverage quality
    methods = [a["extraction_method"] for a in deep_articles]
    if not deep_articles or all(m == "failed" for m in methods):
        coverage = "headlines_only"
    elif all(m == "trafilatura" for m in methods):
        coverage = "full"
    else:
        coverage = "partial"

    # Strip internal fields from headline output
    headline_output = [
        {"title": h["title"], "publisher": h["publisher"], "date": h["date"], "url": h["url"]}
        for h in headlines
    ]

    return {
        "ticker": ticker,
        "timestamp": datetime.now(ET).isoformat(),
        "coverage_quality": coverage,
        "headlines": headline_output,
        "deep_articles": deep_articles,
        "web_search": web_results,
        "sentiment": sentiment,
        "themes": themes,
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser(description="Deep News Research for a stock ticker")
    parser.add_argument("--ticker", required=True, help="Ticker symbol")
    parser.add_argument("--max-articles", type=int, default=3, help="Max articles to extract (default: 3)")
    parser.add_argument("--max-search", type=int, default=5, help="Max web search results (default: 5)")
    args = parser.parse_args()

    ticker = args.ticker.upper()
    result = research(ticker, max_articles=args.max_articles, max_search=args.max_search)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
