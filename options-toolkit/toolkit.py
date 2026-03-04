#!/usr/bin/env python3
"""Options Trading Toolkit - CLI for fetching and analyzing options data."""

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta
from statistics import mean
from zoneinfo import ZoneInfo

import yfinance as yf

# ── Constants ────────────────────────────────────────────────────────────────

ET = ZoneInfo("America/New_York")
MAJOR_DIV = "=" * 40
MINOR_DIV = "\u2500" * 40  # ─

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

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


# ── Utility functions ────────────────────────────────────────────────────────

SCHEDULE = [(9, 31), (11, 0), (12, 30), (14, 0), (15, 0), (15, 59)]
SUMMARY_SCHEDULE = [(16, 1)]


def is_scheduled_time():
    now = datetime.now(ET)
    if now.weekday() >= 5:
        return False
    return (now.hour, now.minute) in SCHEDULE


def is_summary_time():
    now = datetime.now(ET)
    if now.weekday() >= 5:
        return False
    return (now.hour, now.minute) in SUMMARY_SCHEDULE


def select_expiry(expirations, target_dte=120):
    today = date.today()
    def key(exp):
        dte = (date.fromisoformat(exp) - today).days
        return (abs(dte - target_dte), -dte)
    return min(expirations, key=key)


def select_strikes(chain_df, price, count=5):
    atm = round(price)
    all_strikes = sorted(chain_df["strike"].unique())
    all_strikes_list = list(all_strikes)
    nearest = sorted(all_strikes_list, key=lambda s: (abs(s - atm), -s))[:count]
    return sorted(nearest, reverse=True)


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

    # Count Fed and tariff headlines
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


def compute_directional_score(data):
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
        bullish += 1  # contrarian
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


def time_ago(timestamp_str):
    try:
        prev_time = datetime.fromisoformat(timestamp_str)
    except (ValueError, TypeError):
        return "unknown"
    now = datetime.now(ET)
    if prev_time.tzinfo is None:
        prev_time = prev_time.replace(tzinfo=ET)
    diff = now - prev_time
    total_mins = int(diff.total_seconds() / 60)
    if total_mins < 60:
        return f"{total_mins} minutes ago"
    total_hours = total_mins // 60
    if total_hours < 24:
        return f"{total_hours} hours ago"
    total_days = diff.days
    return f"{total_days} days ago"


# ── Fetcher functions ────────────────────────────────────────────────────────

def fetch_price(sym):
    ticker = yf.Ticker(sym)
    try:
        price = ticker.fast_info["lastPrice"]
        prev_close = ticker.fast_info["previousClose"]
    except (KeyError, AttributeError):
        info = ticker.info
        price = info["currentPrice"]
        prev_close = info["previousClose"]
    change = price - prev_close
    change_pct = (change / prev_close) * 100 if prev_close else 0
    now = datetime.now(ET)
    return {
        "ticker": sym,
        "price": price,
        "previous_close": prev_close,
        "change": change,
        "change_pct": change_pct,
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp_iso": now.isoformat(),
    }


def fetch_chain(sym, target_dte=120):
    ticker = yf.Ticker(sym)
    expirations = ticker.options
    if not expirations:
        print(f"No options data available for {sym}", file=sys.stderr)
        sys.exit(1)

    best_expiry = select_expiry(expirations, target_dte)
    dte = (date.fromisoformat(best_expiry) - date.today()).days
    chain = ticker.option_chain(best_expiry)

    price_data = fetch_price(sym)
    price = price_data["price"]
    atm = round(price)

    calls_df = chain.calls
    puts_df = chain.puts
    strikes = select_strikes(calls_df, price, count=10)

    calls = []
    puts = []
    for s in strikes:
        # Calls
        row = calls_df[calls_df["strike"] == s]
        if not row.empty:
            r = row.iloc[0]
            iv = float(r.get("impliedVolatility", 0)) * 100
            calls.append({
                "strike": int(s),
                "iv": round(iv, 2),
                "bid": round(float(r.get("bid", 0)), 2),
                "ask": round(float(r.get("ask", 0)), 2),
                "last": round(float(r.get("lastPrice", 0)), 2),
                "volume": int(r.get("volume", 0) or 0),
                "open_interest": int(r.get("openInterest", 0) or 0),
                "status": "ATM" if int(s) == atm else ("ITM" if s < price else "OTM"),
            })
        # Puts
        row = puts_df[puts_df["strike"] == s]
        if not row.empty:
            r = row.iloc[0]
            iv = float(r.get("impliedVolatility", 0)) * 100
            puts.append({
                "strike": int(s),
                "iv": round(iv, 2),
                "bid": round(float(r.get("bid", 0)), 2),
                "ask": round(float(r.get("ask", 0)), 2),
                "last": round(float(r.get("lastPrice", 0)), 2),
                "volume": int(r.get("volume", 0) or 0),
                "open_interest": int(r.get("openInterest", 0) or 0),
                "status": "ATM" if int(s) == atm else ("ITM" if s > price else "OTM"),
            })

    return {
        "ticker": sym,
        "expiry": best_expiry,
        "dte": dte,
        "atm_strike": atm,
        "current_price": price,
        "previous_close": price_data["previous_close"],
        "change": price_data["change"],
        "change_pct": price_data["change_pct"],
        "timestamp": price_data["timestamp"],
        "timestamp_iso": price_data["timestamp_iso"],
        "calls": calls,
        "puts": puts,
    }


def fetch_news(sym):
    ticker = yf.Ticker(sym)
    articles = ticker.news or []
    # yfinance >= 0.2.31 may return list of dicts with 'content' key
    parsed = []
    for a in articles[:8]:
        url = ""
        summary = ""
        content_type = ""
        if "content" in a and isinstance(a["content"], dict):
            c = a["content"]
            title = c.get("title", a.get("title", ""))
            publisher = c.get("provider", {}).get("displayName", "Unknown") if isinstance(c.get("provider"), dict) else "Unknown"
            pub_time = c.get("pubDate", "")
            # Extract URL from clickThroughUrl or canonical
            ctu = c.get("clickThroughUrl")
            if isinstance(ctu, dict):
                url = ctu.get("url", "")
            elif isinstance(ctu, str):
                url = ctu
            if not url:
                url = c.get("canonicalUrl", {}).get("url", "") if isinstance(c.get("canonicalUrl"), dict) else ""
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
            "title": title, "publisher": publisher, "date": date_str,
            "url": url, "summary": summary, "content_type": content_type,
        })

    score, label, themes, warnings = score_sentiment(parsed)
    return {
        "ticker": sym,
        "headline_count": len(parsed),
        "headlines": parsed,
        "sentiment": {"label": label, "score": score},
        "themes": themes,
        "warnings": warnings,
    }


# ── Storage functions ────────────────────────────────────────────────────────

def _get_file_path(base, ticker, d):
    iso_year, iso_week, _ = d.isocalendar()
    week_dir = os.path.join(base, ticker, f"{iso_year}-W{iso_week:02d}")
    return os.path.join(week_dir, f"{d.isoformat()}.json")


def save_snapshot(sym, data, base_dir=BASE_DIR):
    today = date.today()
    path = _get_file_path(base_dir, sym, today)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        with open(path, "r") as f:
            try:
                snapshots = json.load(f)
            except json.JSONDecodeError:
                snapshots = []
    else:
        snapshots = []
    snapshots.append(data)
    with open(path, "w") as f:
        json.dump(snapshots, f, indent=2)


def load_previous(sym, base_dir=BASE_DIR):
    today = date.today()
    # Step 1: Check today's file
    today_path = _get_file_path(base_dir, sym, today)
    if os.path.exists(today_path):
        try:
            with open(today_path, "r") as f:
                entries = json.load(f)
            if entries and len(entries) >= 1:
                return entries[-1]
        except (json.JSONDecodeError, TypeError):
            pass
    # Steps 2-3: Walk backwards up to 10 days
    for days_back in range(1, 11):
        check_date = today - timedelta(days=days_back)
        check_path = _get_file_path(base_dir, sym, check_date)
        if os.path.exists(check_path):
            try:
                with open(check_path, "r") as f:
                    entries = json.load(f)
                if entries:
                    return entries[-1]
            except (json.JSONDecodeError, TypeError):
                continue
    return None


def load_history(sym, days=5, base_dir=BASE_DIR):
    results = []
    today = date.today()
    days_checked = 0
    days_found = 0
    d = today
    while days_found < days and days_checked < 10:
        path = _get_file_path(base_dir, sym, d)
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    entries = json.load(f)
                if entries:
                    results.append(entries[-1])  # last snapshot of the day
                    days_found += 1
            except (json.JSONDecodeError, TypeError):
                pass
        days_checked += 1
        d -= timedelta(days=1)
    return results


def load_today_snapshots(sym, base_dir=BASE_DIR):
    """Load all snapshots from today."""
    today = date.today()
    path = _get_file_path(base_dir, sym, today)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, TypeError):
        return []


# ── Formatter functions ──────────────────────────────────────────────────────

def _iv_emoji(iv):
    if iv < 20:
        return "\U0001f7e2"  # 🟢
    elif iv <= 35:
        return "\U0001f7e1"  # 🟡
    else:
        return "\U0001f534"  # 🔴


def _price_emoji(change):
    if change > 0:
        return "\U0001f7e2"  # 🟢
    elif change < 0:
        return "\U0001f534"  # 🔴
    return "\U0001f7e1"  # 🟡


def _sign(val):
    return f"+{val}" if val >= 0 else f"{val}"


def _fmt_iv_change(current_iv, prev_strike_data, option_type):
    if prev_strike_data is None:
        return "N/A \U0001f7e1"
    key = f"{option_type}_iv"
    prev_iv = prev_strike_data.get(key)
    if prev_iv is None:
        return "N/A \U0001f7e1"
    abs_change = current_iv - prev_iv
    if prev_iv != 0:
        rel_change = (abs_change / prev_iv) * 100
        text = f"{_sign(round(abs_change, 2))}% ({_sign(round(rel_change, 1))}%)"
    else:
        text = f"{_sign(round(abs_change, 2))}% (N/A)"
    if abs_change > 0:
        return f"{text} \U0001f534"
    elif abs_change < 0:
        return f"{text} \U0001f7e2"
    return "-- \U0001f7e1"


def _status_emoji(status):
    if status == "ITM":
        return "ITM \U0001f7e2"
    elif status == "ATM":
        return "ATM \U0001f7e1"
    return "OTM \U0001f535"


def format_price(data):
    sym = data["ticker"]
    price = data["price"]
    prev = data["previous_close"]
    change = data["change"]
    pct = data["change_pct"]
    emoji = _price_emoji(change)
    ts = data["timestamp"]
    lines = [
        f"Current {sym} Price: ${price:.2f} {emoji} ({_sign(round(change, 2)):>s}${abs(change):.2f} / {_sign(round(pct, 2))}%)",
        f"Previous Close: ${prev:.2f}",
        f"Analysis Time: {ts}",
    ]
    # Fix: the sign and dollar should be like +$0.65 not ++$0.65
    # Redo line 1 properly
    sign_char = "+" if change >= 0 else "-"
    lines[0] = f"Current {sym} Price: ${price:.2f} {emoji} ({sign_char}${abs(change):.2f} / {_sign(round(pct, 2))}%)"
    return "\n".join(lines)


def _fmt_iv_change_compact(current_iv, prev_strike_data, option_type):
    """Return compact IV change string without emoji for card format."""
    if prev_strike_data is None:
        return "N/A"
    key = f"{option_type}_iv"
    prev_iv = prev_strike_data.get(key)
    if prev_iv is None:
        return "N/A"
    abs_change = current_iv - prev_iv
    if prev_iv != 0:
        rel_change = (abs_change / prev_iv) * 100
        return f"{_sign(round(abs_change, 2))}% ({_sign(round(rel_change, 1))}%)"
    return f"{_sign(round(abs_change, 2))}% (N/A)"


def _fmt_strike_card(opt, prev_strikes, option_type, prev_exists):
    """Return 3 lines for a single strike card."""
    status = opt["status"]
    iv = f"{opt['iv']:.2f}%"
    ps = prev_strikes.get(str(opt["strike"])) if prev_strikes else None
    chg = _fmt_iv_change_compact(opt["iv"], ps, option_type) if prev_exists else "N/A"
    bid = f"${opt['bid']:.2f}"
    ask = f"${opt['ask']:.2f}"
    last = f"${opt['last']:.2f}"
    vol = f"{opt['volume']:,}"
    oi = f"{opt['open_interest']:,}"
    return [
        f"${opt['strike']} {status} | IV: {iv}",
        f"  Chg: {chg} | B/A: {bid}/{ask}",
        f"  Last: {last} | Vol: {vol} | OI: {oi}",
    ]


def format_chain(data, prev=None):
    lines = []
    lines.append(f"Target Expiration: {data['expiry']} ({data['dte']} days)")
    lines.append(f"ATM Strike: ${data['atm_strike']}")
    lines.append("")

    prev_strikes = prev.get("strikes", {}) if prev else {}

    # Call table — emoji header outside code block
    lines.append("\U0001f4c8 CALLS")
    lines.append("```")
    for i, c in enumerate(data["calls"]):
        card = _fmt_strike_card(c, prev_strikes, "call", prev is not None)
        lines.extend(card)
        if i < len(data["calls"]) - 1:
            lines.append("")
    lines.append("```")

    # Put table
    lines.append("\U0001f4c9 PUTS")
    lines.append("```")
    for i, p in enumerate(data["puts"]):
        card = _fmt_strike_card(p, prev_strikes, "put", prev is not None)
        lines.extend(card)
        if i < len(data["puts"]) - 1:
            lines.append("")
    lines.append("```")

    return "\n".join(lines)


def format_news(data):
    lines = []
    lines.append(f"\U0001f4f0 LIVE NEWS HEADLINES")
    lines.append(MINOR_DIV)
    lines.append("")

    headlines = data["headlines"]
    if not headlines:
        lines.append("  \u26a0\ufe0f  No news headlines available")
    else:
        lines.append(f"Recent Headlines ({data['headline_count']} articles):")
        for i, h in enumerate(headlines, 1):
            title = h["title"]
            if len(title) > 85:
                title = title[:85] + "..."
            lines.append(f"  {i}. {title}")
            lines.append(f"     {h['publisher']} \u2022 {h['date']}")

    lines.append("")
    sent = data["sentiment"]
    score_str = _sign(sent["score"])
    lines.append(f"News Sentiment: {sent['label']} (Score: {score_str})")
    lines.append(f"Key Themes: {', '.join(data['themes'])}")

    if data["warnings"].get("high_fed_focus"):
        lines.append("  \u26a0\ufe0f  High Fed/monetary policy focus in recent news")
    if data["warnings"].get("high_tariff_focus"):
        lines.append("  \u26a0\ufe0f  High tariff/trade focus in recent news")

    return "\n".join(lines)


def format_history(snapshots, sym):
    if not snapshots:
        return f"No history data found for {sym}"

    lines = []
    lines.append(f"\U0001f4ca IV HISTORY - {sym} (Last {len(snapshots)} Trading Days)")
    lines.append(MINOR_DIV)
    lines.append("")
    lines.append(f"{'Date':<14}{'Price':<11}{'Avg IV':<11}{'Call IV':<11}{'Put IV':<11}{'P/C Vol':<11}{'P/C OI':<11}{'Skew'}")
    for s in snapshots:
        ts = s.get("timestamp", "")
        d = ts[:10] if len(ts) >= 10 else "N/A"
        price = s.get("price", 0)
        avg_iv = s.get("overall_avg_iv", 0)
        call_iv = s.get("avg_call_iv", 0)
        put_iv = s.get("avg_put_iv", 0)
        pc_vol = s.get("pc_vol_ratio", 0)
        pc_oi = s.get("pc_oi_ratio", 0)
        skew = s.get("skew", 0)
        avg_iv_s = f"{avg_iv:.2f}%"
        call_iv_s = f"{call_iv:.2f}%"
        put_iv_s = f"{put_iv:.2f}%"
        skew_s = f"{_sign(round(skew, 2))}%"
        lines.append(
            f"{d:<14}${price:<10.2f}{avg_iv_s:<11}{call_iv_s:<11}"
            f"{put_iv_s:<11}{pc_vol:<11.2f}{pc_oi:<11.2f}{skew_s}"
        )

    # Trend
    if len(snapshots) >= 2:
        newest = snapshots[0].get("overall_avg_iv", 0)
        oldest = snapshots[-1].get("overall_avg_iv", 0)
        change = newest - oldest
        n = len(snapshots)
        if change > 2:
            lines.append(f"\nTrend: IV \u2191 EXPANDING ({_sign(round(change, 2))}% over {n} days)")
        elif change < -2:
            lines.append(f"\nTrend: IV \u2193 CONTRACTING ({_sign(round(change, 2))}% over {n} days)")
        else:
            lines.append(f"\nTrend: IV \u2192 STABLE ({_sign(round(change, 2))}% over {n} days)")

    return "\n".join(lines)


def format_iv_summary(data, prev):
    lines = []
    lines.append(f"\U0001f4ca IMPLIED VOLATILITY SUMMARY")
    lines.append(MINOR_DIV)
    lines.append("")

    avg_call = data.get("avg_call_iv", 0)
    avg_put = data.get("avg_put_iv", 0)
    overall = data.get("overall_avg_iv", 0)

    if prev:
        call_chg = avg_call - prev.get("avg_call_iv", avg_call)
        put_chg = avg_put - prev.get("avg_put_iv", avg_put)
        overall_chg = overall - prev.get("overall_avg_iv", overall)
        call_emoji = "\U0001f534" if call_chg > 0 else "\U0001f7e2"
        put_emoji = "\U0001f534" if put_chg > 0 else "\U0001f7e2"
        overall_emoji = "\U0001f534" if overall_chg > 0 else "\U0001f7e2"
        lines.append(f"Average Call IV:      {avg_call:.2f}%  ({_sign(round(call_chg, 2))}% change) {call_emoji}")
        lines.append(f"Average Put IV:       {avg_put:.2f}%  ({_sign(round(put_chg, 2))}% change) {put_emoji}")
        lines.append(f"Overall Average IV:   {overall:.2f}%")
        lines.append(f"Overall IV Change:    {_sign(round(overall_chg, 2))}% (from previous run) {overall_emoji}")
    else:
        lines.append(f"Average Call IV:      {avg_call:.2f}%")
        lines.append(f"Average Put IV:       {avg_put:.2f}%")
        lines.append(f"Overall Average IV:   {overall:.2f}%")

    lines.append("")
    total_call_vol = data.get("total_call_vol", 0)
    total_put_vol = data.get("total_put_vol", 0)
    pc_vol = data.get("pc_vol_ratio")

    lines.append(f"Total Call Volume:      {total_call_vol:,}")
    lines.append(f"Total Put Volume:       {total_put_vol:,}")
    if pc_vol is not None:
        vol_line = f"Put/Call Vol Ratio:     {pc_vol:.2f}"
        if prev and prev.get("pc_vol_ratio") is not None:
            vol_chg = pc_vol - prev["pc_vol_ratio"]
            vol_emoji = "\U0001f534" if vol_chg > 0 else "\U0001f7e2"
            vol_line += f"  ({_sign(round(vol_chg, 2))} change) {vol_emoji}"
        lines.append(vol_line)
    else:
        lines.append("Put/Call Vol Ratio:     N/A")

    lines.append("")
    total_call_oi = data.get("total_call_oi", 0)
    total_put_oi = data.get("total_put_oi", 0)
    pc_oi = data.get("pc_oi_ratio")

    lines.append(f"Total Call OI:          {total_call_oi:,}")
    lines.append(f"Total Put OI:           {total_put_oi:,}")
    if pc_oi is not None:
        oi_line = f"Put/Call OI Ratio:      {pc_oi:.2f}"
        if prev and prev.get("pc_oi_ratio") is not None:
            oi_chg = pc_oi - prev["pc_oi_ratio"]
            oi_emoji = "\U0001f534" if oi_chg > 0 else "\U0001f7e2"
            oi_line += f"  ({_sign(round(oi_chg, 2))} change) {oi_emoji}"
        lines.append(oi_line)
    else:
        lines.append("Put/Call OI Ratio:      N/A")

    lines.append("")
    skew = data.get("skew", 0)
    skew_line = f"Put/Call IV Skew:       {_sign(round(skew, 2))}%"
    if prev and prev.get("skew") is not None:
        skew_chg = skew - prev["skew"]
        skew_emoji = "\U0001f534" if abs(skew_chg) > 1 else "\U0001f7e1"
        skew_line += f"  ({_sign(round(skew_chg, 2))}% change) {skew_emoji}"
    lines.append(skew_line)

    return "\n".join(lines)




def format_summary(sym, force=False):
    """Generate end-of-day summary comparing open to close."""
    if not force and not is_summary_time():
        return ""

    snapshots = load_today_snapshots(sym)
    if len(snapshots) < 2:
        return ""

    # Skip snapshots with suspect IV (near-zero at market open)
    first = None
    for s in snapshots:
        if s.get("overall_avg_iv", 0) >= 1:
            first = s
            break
    if first is None:
        return ""
    last = snapshots[-1]
    if first is last:
        return ""

    # Price
    open_price = first["price"]
    close_price = last["price"]
    price_change = close_price - open_price
    price_change_pct = (price_change / open_price) * 100 if open_price else 0
    all_prices = [s["price"] for s in snapshots]
    price_high = max(all_prices)
    price_low = min(all_prices)

    # IV
    open_iv = first.get("overall_avg_iv", 0)
    close_iv = last.get("overall_avg_iv", 0)
    iv_change = close_iv - open_iv
    valid_ivs = [s.get("overall_avg_iv", 0) for s in snapshots if s.get("overall_avg_iv", 0) >= 1]
    iv_high = max(valid_ivs) if valid_ivs else close_iv
    iv_low = min(valid_ivs) if valid_ivs else close_iv
    open_call_iv = first.get("avg_call_iv", 0)
    close_call_iv = last.get("avg_call_iv", 0)
    open_put_iv = first.get("avg_put_iv", 0)
    close_put_iv = last.get("avg_put_iv", 0)

    # P/C ratios
    open_pc_vol = first.get("pc_vol_ratio", 0)
    close_pc_vol = last.get("pc_vol_ratio", 0)
    open_pc_oi = first.get("pc_oi_ratio", 0)
    close_pc_oi = last.get("pc_oi_ratio", 0)
    pc_oi_change = close_pc_oi - open_pc_oi

    # Skew
    open_skew = first.get("skew", 0)
    close_skew = last.get("skew", 0)
    skew_change = close_skew - open_skew

    now = datetime.now(ET)
    chunks = []

    # ── Chunk 1: Header + Price ──
    c1 = []
    c1.append(MAJOR_DIV)
    c1.append(f"  \U0001f4ca {sym} END-OF-DAY SUMMARY")
    c1.append(MAJOR_DIV)
    c1.append("")
    c1.append(f"\U0001f4c5 {now.strftime('%Y-%m-%d')} | Market Close")
    c1.append("")
    day_emoji = _price_emoji(price_change)
    sign_char = "+" if price_change >= 0 else "-"
    c1.append("Price Action:")
    c1.append(f"  Open: ${open_price:.2f} \u2192 Close: ${close_price:.2f}")
    c1.append(f"  Day Change: {sign_char}${abs(price_change):.2f} ({_sign(round(price_change_pct, 2))}%) {day_emoji}")
    c1.append(f"  Day Range: ${price_low:.2f} - ${price_high:.2f}")
    c1.append(f"  Snapshots: {len(snapshots)}")
    chunks.append("\n".join(c1))

    # ── Chunk 2: Metrics ──
    c2 = []
    c2.append("\U0001f4c8 INTRADAY METRICS")
    c2.append(MINOR_DIV)
    c2.append("")

    iv_emoji = "\U0001f7e2" if iv_change < 0 else ("\U0001f534" if iv_change > 0 else "\U0001f7e1")
    c2.append("Implied Volatility:")
    c2.append(f"  Open IV: {open_iv:.2f}% \u2192 Close IV: {close_iv:.2f}%")
    c2.append(f"  IV Change: {_sign(round(iv_change, 2))}% {iv_emoji}")
    c2.append(f"  IV Range: {iv_low:.2f}% - {iv_high:.2f}%")
    c2.append(f"  Call IV: {open_call_iv:.2f}% \u2192 {close_call_iv:.2f}%")
    c2.append(f"  Put IV: {open_put_iv:.2f}% \u2192 {close_put_iv:.2f}%")
    c2.append("")

    c2.append("Volume:")
    c2.append(f"  P/C Vol Ratio: {open_pc_vol:.2f} \u2192 {close_pc_vol:.2f}")
    c2.append("")

    c2.append("Open Interest:")
    c2.append(f"  P/C OI Ratio: {open_pc_oi:.2f} \u2192 {close_pc_oi:.2f}")
    c2.append("")

    c2.append("Skew:")
    c2.append(f"  Open: {_sign(round(open_skew, 2))}% \u2192 Close: {_sign(round(close_skew, 2))}%")
    c2.append(f"  Skew Change: {_sign(round(skew_change, 2))}%")
    chunks.append("\n".join(c2))

    # ── Chunk 3: Analysis ──
    c3 = []
    c3.append("\U0001f50d END-OF-DAY ANALYSIS")
    c3.append(MINOR_DIV)
    c3.append("")

    # Technical analysis
    tech = []
    if iv_change < -1:
        tech.append("\u2022 IV contracted \u2014 volatility sellers dominated")
    elif iv_change > 1:
        tech.append("\u2022 IV expanded \u2014 increased uncertainty/fear")
    else:
        tech.append("\u2022 IV stable \u2014 no significant volatility shift")

    if close_pc_vol < 0.8:
        tech.append("\u2022 P/C vol ratio < 0.8 \u2014 call-heavy flow")
    elif close_pc_vol > 1.2:
        tech.append("\u2022 P/C vol ratio > 1.2 \u2014 put-heavy flow")
    else:
        tech.append("\u2022 P/C vol ratio balanced")

    if pc_oi_change < -0.05:
        tech.append("\u2022 P/C OI ratio declining \u2014 call OI gaining vs puts")
    elif pc_oi_change > 0.05:
        tech.append("\u2022 P/C OI ratio rising \u2014 put OI gaining vs calls")
    else:
        tech.append("\u2022 P/C OI ratio stable")

    if skew_change < -0.5:
        tech.append("\u2022 Skew narrowing \u2014 put premium declining")
    elif skew_change > 0.5:
        tech.append("\u2022 Skew widening \u2014 protection demand rising")
    else:
        tech.append("\u2022 Skew stable")

    c3.append("Technical:")
    c3.extend(f"  {t}" for t in tech)
    c3.append("")

    # Market assessment
    mkt = []
    if price_change > 0 and iv_change < 0:
        mkt.append("\u2022 Price up + IV down = healthy rally with confidence")
    elif price_change > 0 and iv_change > 0:
        mkt.append("\u2022 Price up + IV up = rally with hedging demand")
    elif price_change < 0 and iv_change > 0:
        mkt.append("\u2022 Price down + IV up = fear-driven selling")
    elif price_change < 0 and iv_change < 0:
        mkt.append("\u2022 Price down + IV down = orderly pullback")
    else:
        mkt.append("\u2022 Flat session with minimal directional commitment")

    if close_pc_vol < open_pc_vol - 0.1:
        mkt.append("\u2022 Volume sentiment shifted bullish through the day")
    elif close_pc_vol > open_pc_vol + 0.1:
        mkt.append("\u2022 Volume sentiment shifted bearish through the day")

    if abs(price_change_pct) > 1:
        mkt.append(f"\u2022 Significant move ({_sign(round(price_change_pct, 2))}%) \u2014 high conviction day")
    elif abs(price_change_pct) < 0.2:
        mkt.append("\u2022 Tight range \u2014 indecision/consolidation")

    c3.append("Market Assessment:")
    c3.extend(f"  {m}" for m in mkt)
    c3.append("")

    # Day rating
    score = 0
    if price_change > 0:
        score += 1
    if price_change < 0:
        score -= 1
    if iv_change < 0:
        score += 1
    if iv_change > 0:
        score -= 1
    if close_pc_vol < 0.9:
        score += 1
    if close_pc_vol > 1.1:
        score -= 1
    if pc_oi_change < -0.05:
        score += 1
    if pc_oi_change > 0.05:
        score -= 1
    if skew_change < -0.3:
        score += 1
    if skew_change > 0.3:
        score -= 1

    if score >= 3:
        rating = "BULLISH \U0001f7e2"
    elif score >= 1:
        rating = "SLIGHTLY BULLISH \U0001f7e2"
    elif score <= -3:
        rating = "BEARISH \U0001f534"
    elif score <= -1:
        rating = "SLIGHTLY BEARISH \U0001f534"
    else:
        rating = "NEUTRAL \U0001f7e1"

    c3.append(f"Day Rating: {rating}")
    c3.append("")
    c3.append(MAJOR_DIV)
    c3.append("\u2705 END-OF-DAY SUMMARY COMPLETE")
    c3.append(MAJOR_DIV)
    chunks.append("\n".join(c3))

    return "\n---SPLIT---\n".join(chunks)


def format_report(sym, force=False):
    # Market hours check
    if not force and not is_scheduled_time():
        return ""

    # Fetch data
    chain_data = fetch_chain(sym)
    prev = load_previous(sym)

    price = chain_data["current_price"]

    # Select closest 5 strikes to current price for the report
    all_call_strikes = {c["strike"] for c in chain_data["calls"]}
    report_strikes = sorted(
        all_call_strikes, key=lambda s: (abs(s - round(price)), -s)
    )[:5]
    report_strikes_set = set(report_strikes)
    calls = [c for c in chain_data["calls"] if c["strike"] in report_strikes_set]
    puts = [p for p in chain_data["puts"] if p["strike"] in report_strikes_set]
    calls.sort(key=lambda c: -c["strike"])
    puts.sort(key=lambda p: -p["strike"])

    # Compute derived values
    avg_call_iv = mean([c["iv"] for c in calls]) if calls else 0
    avg_put_iv = mean([p["iv"] for p in puts]) if puts else 0
    overall_avg_iv = (avg_call_iv + avg_put_iv) / 2
    skew = avg_put_iv - avg_call_iv

    total_call_vol = sum(c["volume"] for c in calls)
    total_put_vol = sum(p["volume"] for p in puts)
    pc_vol_ratio = total_put_vol / total_call_vol if total_call_vol > 0 else None

    total_call_oi = sum(c["open_interest"] for c in calls)
    total_put_oi = sum(p["open_interest"] for p in puts)
    pc_oi_ratio = total_put_oi / total_call_oi if total_call_oi > 0 else None

    # Build enriched data dict (use filtered 5-strike calls/puts for report)
    data = {**chain_data}
    data["calls"] = calls
    data["puts"] = puts
    data["avg_call_iv"] = round(avg_call_iv, 2)
    data["avg_put_iv"] = round(avg_put_iv, 2)
    data["overall_avg_iv"] = round(overall_avg_iv, 2)
    data["skew"] = round(skew, 2)
    data["total_call_vol"] = total_call_vol
    data["total_put_vol"] = total_put_vol
    data["pc_vol_ratio"] = round(pc_vol_ratio, 2) if pc_vol_ratio is not None else None
    data["total_call_oi"] = total_call_oi
    data["total_put_oi"] = total_put_oi
    data["pc_oi_ratio"] = round(pc_oi_ratio, 2) if pc_oi_ratio is not None else None

    # Changes from previous
    if prev:
        data["overall_iv_change"] = round(overall_avg_iv - prev.get("overall_avg_iv", overall_avg_iv), 2)
        data["avg_call_iv_change"] = round(avg_call_iv - prev.get("avg_call_iv", avg_call_iv), 2)
        data["avg_put_iv_change"] = round(avg_put_iv - prev.get("avg_put_iv", avg_put_iv), 2)
    else:
        data["overall_iv_change"] = None
        data["avg_call_iv_change"] = None
        data["avg_put_iv_change"] = None

    # Build snapshot for saving (use all fetched strikes, not just report 5)
    now = datetime.now(ET)
    snapshot = {
        "timestamp": now.isoformat(),
        "price": price,
        "prev_close": chain_data["previous_close"],
        "expiry": chain_data["expiry"],
        "avg_call_iv": data["avg_call_iv"],
        "avg_put_iv": data["avg_put_iv"],
        "overall_avg_iv": data["overall_avg_iv"],
        "pc_vol_ratio": data["pc_vol_ratio"] if data["pc_vol_ratio"] is not None else 0,
        "pc_oi_ratio": data["pc_oi_ratio"] if data["pc_oi_ratio"] is not None else 0,
        "skew": data["skew"],
        "strikes": {},
    }
    for c in chain_data["calls"]:
        s = str(c["strike"])
        snapshot["strikes"].setdefault(s, {})
        snapshot["strikes"][s]["call_iv"] = c["iv"]
        snapshot["strikes"][s]["call_vol"] = c["volume"]
        snapshot["strikes"][s]["call_oi"] = c["open_interest"]
    for p in chain_data["puts"]:
        s = str(p["strike"])
        snapshot["strikes"].setdefault(s, {})
        snapshot["strikes"][s]["put_iv"] = p["iv"]
        snapshot["strikes"][s]["put_vol"] = p["volume"]
        snapshot["strikes"][s]["put_oi"] = p["open_interest"]

    # Build report sections
    chunks = []

    # Chunk 1: History check + Header + Price
    chunk1_lines = []
    if prev:
        ts = prev.get("timestamp", "")
        ts_display = ts.replace("T", " ")[:19] if ts else "unknown"
        chunk1_lines.append(f"\u2713 Previous data from: {ts_display} ({time_ago(ts)})")
    else:
        chunk1_lines.append("\u2139\ufe0f  No previous IV data found - first run")
    chunk1_lines.append("")
    chunk1_lines.append(MAJOR_DIV)
    chunk1_lines.append(f"  \U0001f3af {sym} OPTIONS TRADING ANALYZER")
    chunk1_lines.append(MAJOR_DIV)
    chunk1_lines.append("")

    # Price section
    price_data = {
        "ticker": sym,
        "price": price,
        "previous_close": chain_data["previous_close"],
        "change": chain_data["change"],
        "change_pct": chain_data["change_pct"],
        "timestamp": chain_data["timestamp"],
    }
    chunk1_lines.append(format_price(price_data))
    chunks.append("\n".join(chunk1_lines))

    # Chunk 2: Options tables
    chunks.append(format_chain(data, prev))

    # Chunk 3: IV Summary + Footer
    iv_chunk = format_iv_summary(data, prev)
    iv_chunk += "\n\n" + MAJOR_DIV + "\n\u2705 REPORT COMPLETE\n" + MAJOR_DIV
    iv_chunk += "\n\n\u2713 Saved IV data for next comparison"
    chunks.append(iv_chunk)

    # Save snapshot
    save_snapshot(sym, snapshot)

    return "\n---SPLIT---\n".join(chunks)


# ── Subcommand handlers ──────────────────────────────────────────────────────

def cmd_price(args):
    sym = args.ticker.upper()
    try:
        data = fetch_price(sym)
    except Exception as e:
        print(f"Error fetching price for {sym}: {e}", file=sys.stderr)
        sys.exit(1)
    if args.json:
        out = {
            "ticker": data["ticker"],
            "price": data["price"],
            "previous_close": data["previous_close"],
            "change": round(data["change"], 2),
            "change_pct": round(data["change_pct"], 2),
            "timestamp": data["timestamp_iso"],
        }
        print(json.dumps(out, indent=2))
    else:
        print(format_price(data))


def cmd_chain(args):
    sym = args.ticker.upper()
    try:
        data = fetch_chain(sym, target_dte=args.dte)
    except Exception as e:
        print(f"Error fetching chain for {sym}: {e}", file=sys.stderr)
        sys.exit(1)
    if args.json:
        out = {
            "ticker": data["ticker"],
            "expiry": data["expiry"],
            "dte": data["dte"],
            "atm_strike": data["atm_strike"],
            "current_price": data["current_price"],
            "calls": data["calls"],
            "puts": data["puts"],
        }
        print(json.dumps(out, indent=2))
    else:
        print(format_chain(data))


def cmd_news(args):
    sym = args.ticker.upper()
    try:
        data = fetch_news(sym)
    except Exception as e:
        print(f"Error fetching news for {sym}: {e}", file=sys.stderr)
        sys.exit(1)
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(format_news(data))


def cmd_history(args):
    sym = args.ticker.upper()
    try:
        snapshots = load_history(sym, days=args.days)
    except Exception as e:
        print(f"Error loading history for {sym}: {e}", file=sys.stderr)
        sys.exit(1)
    if args.json:
        out = {
            "ticker": sym,
            "days_requested": args.days,
            "days_found": len(snapshots),
            "snapshots": snapshots,
        }
        if len(snapshots) >= 2:
            newest = snapshots[0].get("overall_avg_iv", 0)
            oldest = snapshots[-1].get("overall_avg_iv", 0)
            change = newest - oldest
            if change > 2:
                direction = "EXPANDING"
            elif change < -2:
                direction = "CONTRACTING"
            else:
                direction = "STABLE"
            out["trend"] = {"direction": direction, "change": round(change, 2), "period_days": len(snapshots)}
        print(json.dumps(out, indent=2))
    else:
        print(format_history(snapshots, sym))


def cmd_summary(args):
    sym = args.ticker.upper()
    try:
        output = format_summary(sym, force=args.force)
    except Exception as e:
        print(f"Error generating summary for {sym}: {e}", file=sys.stderr)
        sys.exit(1)
    if output:
        print(output)


def cmd_report(args):
    sym = args.ticker.upper()
    try:
        output = format_report(sym, force=args.force)
    except Exception as e:
        print(f"Error generating report for {sym}: {e}", file=sys.stderr)
        sys.exit(1)
    if output:
        if args.json:
            # For JSON mode, we'd need to build structured data
            # For now, output text (JSON report mode is a future enhancement)
            chain_data = fetch_chain(sym)
            prev = load_previous(sym)
            calls = chain_data["calls"]
            puts = chain_data["puts"]
            avg_call_iv = mean([c["iv"] for c in calls]) if calls else 0
            avg_put_iv = mean([p["iv"] for p in puts]) if puts else 0
            overall = (avg_call_iv + avg_put_iv) / 2
            total_call_vol = sum(c["volume"] for c in calls)
            total_put_vol = sum(p["volume"] for p in puts)
            total_call_oi = sum(c["open_interest"] for c in calls)
            total_put_oi = sum(p["open_interest"] for p in puts)
            pc_vol = total_put_vol / total_call_vol if total_call_vol else None
            pc_oi = total_put_oi / total_call_oi if total_call_oi else None
            skew = avg_put_iv - avg_call_iv

            score_data = {
                "overall_avg_iv": overall,
                "skew": skew,
                "pc_vol_ratio": pc_vol,
                "pc_oi_ratio": pc_oi,
                "dte": chain_data["dte"],
                "overall_iv_change": (overall - prev.get("overall_avg_iv", overall)) if prev else None,
            }
            b, be = compute_directional_score(score_data)
            if b > be + 1:
                rec = "BUY CALLS"
            elif be > b + 1:
                rec = "BUY PUTS"
            else:
                rec = "WAIT OR STRADDLE"

            out = {
                "ticker": sym,
                "timestamp": chain_data["timestamp_iso"],
                "price": {
                    "current": chain_data["current_price"],
                    "prev_close": chain_data["previous_close"],
                    "change": round(chain_data["change"], 2),
                    "change_pct": round(chain_data["change_pct"], 2),
                },
                "expiry": {"date": chain_data["expiry"], "dte": chain_data["dte"]},
                "atm_strike": chain_data["atm_strike"],
                "calls": calls,
                "puts": puts,
                "iv_summary": {
                    "avg_call_iv": round(avg_call_iv, 2),
                    "avg_put_iv": round(avg_put_iv, 2),
                    "overall_avg_iv": round(overall, 2),
                    "skew": round(skew, 2),
                },
                "volumes": {
                    "total_call": total_call_vol,
                    "total_put": total_put_vol,
                    "pc_ratio": round(pc_vol, 2) if pc_vol else None,
                },
                "oi": {
                    "total_call": total_call_oi,
                    "total_put": total_put_oi,
                    "pc_ratio": round(pc_oi, 2) if pc_oi else None,
                },
                "directional_score": {"bullish": b, "bearish": be},
                "recommendation": rec,
                "previous_run": {
                    "timestamp": prev.get("timestamp") if prev else None,
                    "overall_avg_iv": prev.get("overall_avg_iv") if prev else None,
                },
            }
            print(json.dumps(out, indent=2))
        else:
            print(output)


# ── CLI entry point ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Options Trading Toolkit")
    sub = parser.add_subparsers(dest="command", required=True)

    # price
    p_price = sub.add_parser("price", help="Current stock price")
    p_price.add_argument("--ticker", required=True, help="Ticker symbol")
    p_price.add_argument("--json", action="store_true", help="JSON output")

    # chain
    p_chain = sub.add_parser("chain", help="Options chain")
    p_chain.add_argument("--ticker", required=True, help="Ticker symbol")
    p_chain.add_argument("--dte", type=int, default=120, help="Target DTE")
    p_chain.add_argument("--json", action="store_true", help="JSON output")

    # news
    p_news = sub.add_parser("news", help="News headlines")
    p_news.add_argument("--ticker", required=True, help="Ticker symbol")
    p_news.add_argument("--json", action="store_true", help="JSON output")

    # history
    p_hist = sub.add_parser("history", help="IV history")
    p_hist.add_argument("--ticker", required=True, help="Ticker symbol")
    p_hist.add_argument("--days", type=int, default=5, help="Days to look back")
    p_hist.add_argument("--json", action="store_true", help="JSON output")

    # report
    p_report = sub.add_parser("report", help="Full analysis report")
    p_report.add_argument("--ticker", required=True, help="Ticker symbol")
    p_report.add_argument("--force", action="store_true", help="Skip market hours check")
    p_report.add_argument("--json", action="store_true", help="JSON output")

    # summary
    p_summary = sub.add_parser("summary", help="End-of-day summary")
    p_summary.add_argument("--ticker", required=True, help="Ticker symbol")
    p_summary.add_argument("--force", action="store_true", help="Skip schedule check")

    args = parser.parse_args()

    handlers = {
        "price": cmd_price,
        "chain": cmd_chain,
        "news": cmd_news,
        "history": cmd_history,
        "report": cmd_report,
        "summary": cmd_summary,
    }
    handlers[args.command](args)


if __name__ == "__main__":
    main()
