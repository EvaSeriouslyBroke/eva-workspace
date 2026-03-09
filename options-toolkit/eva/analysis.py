"""Analysis — trends, chain summary, IV rank, sentiment, directional scoring."""

from statistics import mean


# ── Sentiment constants ──────────────────────────────────────────────────────

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


# ── Sentiment scoring ────────────────────────────────────────────────────────

def score_sentiment(articles):
    """Score headlines for bullish/bearish sentiment.

    Returns (score, label, themes, warnings).
    """
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

    warnings = {}
    fed_count = sum(1 for a in articles
                    if any(kw in a.get("title", "").lower()
                           for kw in THEME_MAP["Federal Reserve Policy"]))
    tariff_count = sum(1 for a in articles
                       if any(kw in a.get("title", "").lower()
                              for kw in THEME_MAP["Trade/Tariffs"]))
    warnings["high_fed_focus"] = fed_count >= 2
    warnings["high_tariff_focus"] = tariff_count >= 2

    return total, label, themes, warnings


# ── Directional scoring ──────────────────────────────────────────────────────

def compute_directional_score(data):
    """Rate bullish/bearish conditions from options data."""
    bullish = 2
    bearish = 2

    dte = data.get("dte", 120)
    if dte <= 60:
        bearish += 1
    elif dte > 120:
        bullish += 1

    overall_iv = data.get("overall_avg_iv", 25)
    if overall_iv <= 15:
        bullish += 2
        bearish += 2
    elif overall_iv > 35:
        bullish -= 1
        bearish -= 1

    iv_change = data.get("overall_iv_change")
    if iv_change is not None:
        if iv_change < -2:
            bullish += 2
            bearish += 2
        elif iv_change > 2:
            bullish -= 1
            bearish -= 1

    skew = data.get("skew", 0)
    if skew > 5:
        bullish += 1
    elif skew > 2:
        bearish += 1
    elif skew < -2:
        bullish += 1

    pc_vol = data.get("pc_vol_ratio")
    if pc_vol is not None:
        if pc_vol < 0.8:
            bullish += 2
        elif pc_vol > 1.2:
            bearish += 2

    pc_oi = data.get("pc_oi_ratio")
    if pc_oi is not None:
        if pc_oi < 0.8:
            bullish += 1
        elif pc_oi > 1.2:
            bearish += 1

    return max(bullish, 0), max(bearish, 0)


# ── Numeric helpers ──────────────────────────────────────────────────────────

def _num(v):
    """Coerce a value to float, treating None/NaN as 0."""
    if v is None:
        return 0
    try:
        f = float(v)
        if f != f:  # NaN check
            return 0
        return f
    except (ValueError, TypeError):
        return 0


# ── Price trend computation ──────────────────────────────────────────────────

def compute_trends(history_data, current_price):
    """Compute 52-week range, SMAs, and percentage returns from daily history."""
    if not history_data:
        return {}

    closes = [_num(d.get("close")) for d in history_data if _num(d.get("close")) > 0]
    highs = [_num(d.get("high")) for d in history_data if _num(d.get("high")) > 0]
    lows = [_num(d.get("low")) for d in history_data if _num(d.get("low")) > 0]

    if not closes:
        return {}

    high_52w = max(highs) if highs else current_price
    low_52w = min(lows) if lows else current_price
    range_52w = high_52w - low_52w if high_52w > low_52w else 1

    sma_50 = sum(closes[-50:]) / len(closes[-50:]) if len(closes) >= 50 else None
    sma_200 = sum(closes[-200:]) / len(closes[-200:]) if len(closes) >= 200 else None

    if sma_50 and sma_200:
        if current_price > sma_50 and current_price > sma_200:
            sma_signal = "above_both"
        elif current_price < sma_50 and current_price < sma_200:
            sma_signal = "below_both"
        else:
            sma_signal = "mixed"
    else:
        sma_signal = "insufficient_data"

    def pct_return(n):
        if len(closes) > n:
            old = closes[-(n+1)]
            return round((current_price - old) / old * 100, 1) if old else None
        return None

    returns = {}
    for label, n in [("1w", 5), ("1m", 21), ("3m", 63), ("6m", 126), ("1y", 252)]:
        r = pct_return(n)
        if r is not None:
            returns[label] = r

    parts = []
    if sma_signal == "above_both":
        parts.append("Uptrend — above 50 and 200 SMA")
    elif sma_signal == "below_both":
        parts.append("Downtrend — below 50 and 200 SMA")
    else:
        parts.append("Mixed — between 50 and 200 SMA")
    if "1y" in returns:
        direction = "up" if returns["1y"] >= 0 else "down"
        parts.append(f"{direction} {abs(returns['1y'])}% over 12 months")

    return {
        "price_52w_high": round(high_52w, 2),
        "price_52w_low": round(low_52w, 2),
        "price_vs_52w_pct": round((current_price - low_52w) / range_52w * 100),
        "sma_50": round(sma_50, 2) if sma_50 else None,
        "sma_200": round(sma_200, 2) if sma_200 else None,
        "sma_signal": sma_signal,
        "returns": returns,
        "trend_summary": ", ".join(parts),
    }


# ── Chain summary builder ───────────────────────────────────────────────────

def build_chain_summary(chain_data, current_price):
    """Summarize near-the-money calls/puts from raw Tradier chain data."""
    if not chain_data:
        return {}

    calls = [o for o in chain_data if o.get("option_type") == "call"]
    puts = [o for o in chain_data if o.get("option_type") == "put"]

    # Near-money: within 5% of current price
    margin = current_price * 0.05
    near_calls = [c for c in calls if abs(c.get("strike", 0) - current_price) <= margin]
    near_puts = [p for p in puts if abs(p.get("strike", 0) - current_price) <= margin]

    def avg_iv(options):
        ivs = [o.get("greeks", {}).get("mid_iv") or o.get("greeks", {}).get("smv_vol", 0)
               for o in options if o.get("greeks")]
        ivs = [iv for iv in ivs if iv and iv > 0]
        return round(sum(ivs) / len(ivs) * 100, 1) if ivs else None

    call_vol = sum(c.get("volume", 0) or 0 for c in calls)
    put_vol = sum(p.get("volume", 0) or 0 for p in puts)
    pc_ratio = round(put_vol / call_vol, 2) if call_vol > 0 else None

    def make_summaries(options, limit=5):
        result = []
        for o in sorted(options, key=lambda x: x.get("strike", 0))[:limit]:
            greeks = o.get("greeks", {})
            result.append({
                "strike": o.get("strike"),
                "bid": o.get("bid"),
                "ask": o.get("ask"),
                "iv": round((greeks.get("mid_iv") or greeks.get("smv_vol", 0) or 0) * 100, 1),
                "delta": round(greeks.get("delta", 0) or 0, 3),
                "gamma": round(greeks.get("gamma", 0) or 0, 4),
                "theta": round(greeks.get("theta", 0) or 0, 4),
                "vega": round(greeks.get("vega", 0) or 0, 4),
                "rho": round(greeks.get("rho", 0) or 0, 4),
                "volume": o.get("volume", 0),
                "open_interest": o.get("open_interest", 0),
            })
        return result

    return {
        "near_money_calls": make_summaries(near_calls),
        "near_money_puts": make_summaries(near_puts),
        "avg_call_iv": avg_iv(near_calls),
        "avg_put_iv": avg_iv(near_puts),
        "pc_vol_ratio": pc_ratio,
    }


# ── IV rank ──────────────────────────────────────────────────────────────────

def compute_iv_rank(current_iv, iv_history):
    """Compute IV rank (0-100) and percentile from history.

    IV Rank = (current - 52w low) / (52w high - 52w low) * 100
    """
    if not iv_history or not current_iv:
        return None, None
    ivs = [iv for _, iv in iv_history]
    iv_high = max(ivs)
    iv_low = min(ivs)
    iv_range = iv_high - iv_low
    rank = round((current_iv - iv_low) / iv_range * 100) if iv_range > 0 else 50
    rank = max(0, min(100, rank))
    pct = round(sum(1 for iv in ivs if iv < current_iv) / len(ivs) * 100)
    return rank, pct
