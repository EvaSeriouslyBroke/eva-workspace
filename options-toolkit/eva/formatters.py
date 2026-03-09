"""Formatters — all report, chain, summary, status, and history formatting."""

from datetime import date, datetime
from statistics import mean

from eva import ET, MAJOR_DIV, MINOR_DIV
from eva.analysis import compute_directional_score, score_sentiment, _num
from eva.evaluate import order_option_info
from eva.storage import load_today_snapshots, load_previous, save_snapshot
from eva.symbols import parse_occ_symbol
from eva.tradier import fetch_options_chain, fetch_price, normalize_list


# ── Schedule constants ────────────────────────────────────────────────────────

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


# ── Time helper ───────────────────────────────────────────────────────────────

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


# ── Emoji helpers ─────────────────────────────────────────────────────────────

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


def _status_emoji(status):
    if status == "ITM":
        return "ITM \U0001f7e2"
    elif status == "ATM":
        return "ATM \U0001f7e1"
    return "OTM \U0001f535"


# ── IV change formatting ─────────────────────────────────────────────────────

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


# ── Strike card formatting ───────────────────────────────────────────────────

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


# ── Price formatter ───────────────────────────────────────────────────────────

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


# ── Chain formatter ───────────────────────────────────────────────────────────

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


# ── News formatter ────────────────────────────────────────────────────────────

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


# ── IV history formatter (from toolkit.py format_history) ─────────────────────

def format_history_iv(snapshots, sym):
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


# ── IV summary formatter ─────────────────────────────────────────────────────

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


# ── End-of-day summary (fetches + formats) ────────────────────────────────────

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


# ── Full report (fetches + formats) ──────────────────────────────────────────

def format_report(cfg, sym, force=False):
    # Market hours check
    if not force and not is_scheduled_time():
        return ""

    # Fetch data
    chain_data = fetch_options_chain(cfg, sym)
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


# ── Portfolio status formatter (from trading.py) ──────────────────────────────

def format_status(balances, positions, orders):
    """Format portfolio status for Discord."""
    lines = [
        MAJOR_DIV,
        "  \U0001f4b0 EVA'S PAPER TRADING PORTFOLIO",
        MAJOR_DIV,
        "",
    ]

    # Balances
    lines.append(f"\U0001f4b5 Cash: ${balances.get('cash', 0):,.2f}")
    if balances.get("unsettled_funds", 0) > 0:
        lines.append(f"  \u23f3 Unsettled: ${balances['unsettled_funds']:,.2f}")
        lines.append(f"  \u2705 Settled: ${balances['settled_cash']:,.2f}")
    lines.append(f"\U0001f4ca Portfolio Value: ${balances.get('market_value', 0):,.2f}")
    lines.append(f"\U0001f4c8 Total Equity: ${balances.get('total_equity', 0):,.2f}")
    lines.append("")

    # Positions
    pos_list = normalize_list(positions)
    lines.append(f"\U0001f4cb OPEN POSITIONS ({len(pos_list)})")
    lines.append(MINOR_DIV)
    if not pos_list:
        lines.append("No open positions.")
    else:
        for p in pos_list:
            sym = p.get("symbol", "")
            parsed = parse_occ_symbol(sym) if sym else {}
            qty = p.get("quantity", 0)
            cost = p.get("cost_basis", 0) or 0

            strike = parsed.get("strike", "?")
            opt_type = parsed.get("type", "?").title()
            expiry = parsed.get("expiry", "?")
            ticker = parsed.get("ticker", "?")

            # Format expiry as Mon DD
            try:
                exp_dt = datetime.strptime(expiry, "%Y-%m-%d")
                exp_str = exp_dt.strftime("%b %d")
                dte = (exp_dt.date() - date.today()).days
            except Exception:
                exp_str = expiry
                dte = "?"

            lines.append(f"{ticker} ${strike} {opt_type} \u2014 {exp_str} ({dte} DTE)")
            lines.append(f"  Qty: {qty} | Cost: ${cost:,.2f}")

            # P&L if available
            close_price = p.get("close", 0) or 0
            if close_price and cost:
                mkt_val = abs(qty) * close_price * 100
                pnl = mkt_val - cost
                pnl_pct = pnl / cost * 100 if cost else 0
                emoji = "\U0001f7e2" if pnl >= 0 else "\U0001f534"
                sign = "+" if pnl >= 0 else ""
                lines.append(f"  Value: ${mkt_val:,.2f} | P&L: {sign}${pnl:,.2f} ({sign}{pnl_pct:.1f}%) {emoji}")
            lines.append("")

    # Today's orders
    today_str = date.today().isoformat()
    today_orders = [o for o in orders if str(o.get("create_date", "")).startswith(today_str)]
    if today_orders:
        lines.append(f"\U0001f4ca TODAY'S ORDERS")
        lines.append(MINOR_DIV)
        for o in today_orders:
            status = o.get("status", "unknown")
            opt_sym, opt_side = order_option_info(o)

            status_emoji = {
                "filled": "\u2705",
                "pending": "\u23f3",
                "open": "\u23f3",
                "partially_filled": "\u23f3",
                "canceled": "\u274c",
                "rejected": "\u274c",
                "expired": "\u23f0",
            }.get(status, "\u2753")

            action = "BUY" if "buy" in opt_side else "SELL"
            parsed = parse_occ_symbol(opt_sym) if opt_sym else {}
            ticker = parsed.get("ticker", "?")
            strike = parsed.get("strike", "?")
            opt_type = "C" if parsed.get("type") == "call" else "P"
            expiry = parsed.get("expiry", "?")
            try:
                exp_short = datetime.strptime(expiry, "%Y-%m-%d").strftime("%b%d")
            except Exception:
                exp_short = expiry

            avg_price = o.get("avg_fill_price", "?")
            lines.append(f"{status_emoji} {action} {ticker} ${strike}{opt_type} {exp_short} \u2014 {status.title()} @ ${avg_price}")
        lines.append("")

    return "\n".join(lines)


# ── Trade history formatter (from trading.py format_history) ──────────────────

def format_trade_history(orders, reasons, limit=20):
    """Format order history with reasoning."""
    lines = [
        MAJOR_DIV,
        "  \U0001f4dc PAPER TRADE HISTORY",
        MAJOR_DIV,
        "",
    ]

    if not orders:
        lines.append("No orders yet.")
        return "\n".join(lines)

    for o in orders[:limit]:
        oid = str(o.get("id", ""))
        status = o.get("status", "unknown")
        created = o.get("create_date", "?")
        try:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            created_str = dt.strftime("%m/%d %H:%M")
        except Exception:
            created_str = str(created)[:10]

        opt_sym, opt_side = order_option_info(o)
        action = "BUY" if "buy" in opt_side else "SELL" if "sell" in opt_side else "?"
        parsed = parse_occ_symbol(opt_sym) if opt_sym else {}
        ticker = parsed.get("ticker", "?")
        strike = parsed.get("strike", "?")
        opt_type = parsed.get("type", "?").title()
        expiry = parsed.get("expiry", "?")

        avg_price = o.get("avg_fill_price", "?")
        qty = o.get("quantity", "?")

        status_emoji = "\u2705" if status == "filled" else "\u274c" if status in ("canceled", "rejected") else "\u23f3"
        lines.append(f"{status_emoji} {created_str} | {action} {qty}x {ticker} ${strike} {opt_type} {expiry}")
        lines.append(f"   Status: {status.title()} | Fill: ${avg_price}")

        # Add reason if we have one
        if oid in reasons:
            reason_text = reasons[oid].get("reason", "")
            if reason_text:
                lines.append(f"   Reason: {reason_text}")
        lines.append("")

    return "\n".join(lines)
