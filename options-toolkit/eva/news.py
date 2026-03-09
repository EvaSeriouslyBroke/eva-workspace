"""News headlines (DuckDuckGo) and deep research (trafilatura)."""

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from eva import ET
from eva.analysis import score_sentiment


# ── Headline fetching via DuckDuckGo ─────────────────────────────────────────

def fetch_headlines(ticker, max_results=8):
    """Fetch news headlines from DuckDuckGo news search."""
    try:
        import warnings
        warnings.filterwarnings("ignore", message=".*has been renamed.*")
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.news(f"{ticker} stock news", max_results=max_results))
    except Exception as e:
        print(f"Warning: DuckDuckGo news search failed: {e}", file=sys.stderr)
        results = []

    parsed = []
    for r in results:
        date_str = "N/A"
        raw_date = r.get("date", "")
        if raw_date:
            try:
                # DDGS returns dates like "2026-03-09T14:30:00+00:00"
                dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                date_str = "N/A"
        parsed.append({
            "title": r.get("title", ""),
            "publisher": r.get("source", "Unknown"),
            "date": date_str,
            "url": r.get("url", ""),
            "summary": r.get("body", ""),
            "content_type": "",
        })
    return parsed


def fetch_news(cfg, ticker):
    """Fetch headlines and score sentiment. Returns formatted dict for display."""
    headlines = fetch_headlines(ticker)
    score, label, themes, warnings = score_sentiment(headlines)
    return {
        "ticker": ticker,
        "headline_count": len(headlines),
        "headlines": headlines,
        "sentiment": {"label": label, "score": score},
        "themes": themes,
        "warnings": warnings,
    }


# ── Article content extraction ───────────────────────────────────────────────

def extract_article(article, max_content=3000):
    """Extract full article content using trafilatura."""
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
        result["content"] = article.get("summary", "")[:max_content]
        if result["content"]:
            result["extraction_method"] = "summary_fallback"
        return result, error_msg

    fallback = article.get("summary", "")[:max_content]
    if fallback:
        result["content"] = fallback
        result["extraction_method"] = "summary_fallback"
        return result, f"Article extraction failed for {article['publisher']} (empty content, used summary)"
    return result, f"Article extraction failed for {article['publisher']} (no content available)"


def extract_articles_concurrent(articles, max_articles=3, max_content=3000):
    """Extract content from top articles concurrently."""
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


# ── Web search ───────────────────────────────────────────────────────────────

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


# ── Deep research orchestrator ───────────────────────────────────────────────

def research(ticker, max_articles=3, max_search=5):
    """Run full deep news research for a ticker. Returns dict."""
    errors = []

    try:
        headlines = fetch_headlines(ticker)
    except Exception as e:
        print(f"Error fetching headlines for {ticker}: {e}", file=sys.stderr)
        sys.exit(1)

    deep_articles, extraction_errors = extract_articles_concurrent(
        headlines, max_articles=max_articles
    )
    errors.extend(extraction_errors)

    web_results, search_error = search_web(ticker, max_results=max_search)
    if search_error:
        errors.append(search_error)

    score, label, themes, _ = score_sentiment(headlines)

    methods = [a["extraction_method"] for a in deep_articles]
    if not deep_articles or all(m == "failed" for m in methods):
        coverage = "headlines_only"
    elif all(m == "trafilatura" for m in methods):
        coverage = "full"
    else:
        coverage = "partial"

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
        "sentiment": {"label": label, "score": score},
        "themes": themes,
        "errors": errors,
    }
