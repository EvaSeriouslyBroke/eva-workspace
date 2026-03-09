"""All file persistence — snapshots, reasons, positions, log, IV, news."""

import json
import os
from datetime import date, datetime, timedelta

from eva import BASE_DIR, ET


# ── Mode-aware base directories ──────────────────────────────────────────────

def market_data_dir(mode):
    """Return the market data base directory for a trading mode.

    Paper and live modes store market data separately because Tradier sandbox
    data is 15-minute delayed vs real-time for live.
    """
    return os.path.join(BASE_DIR, mode)


# ── Report snapshot storage (data/{mode}/{TICKER}/{YYYY}-W{WW}/{date}.json) ──

def _get_file_path(base, ticker, d):
    iso_year, iso_week, _ = d.isocalendar()
    week_dir = os.path.join(base, ticker, f"{iso_year}-W{iso_week:02d}")
    return os.path.join(week_dir, f"{d.isoformat()}.json")


def save_snapshot(sym, data, mode="paper"):
    today = date.today()
    path = _get_file_path(market_data_dir(mode), sym, today)
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


def load_previous(sym, mode="paper"):
    base = market_data_dir(mode)
    today = date.today()
    today_path = _get_file_path(base, sym, today)
    if os.path.exists(today_path):
        try:
            with open(today_path, "r") as f:
                entries = json.load(f)
            if entries and len(entries) >= 1:
                return entries[-1]
        except (json.JSONDecodeError, TypeError):
            pass
    for days_back in range(1, 11):
        check_date = today - timedelta(days=days_back)
        check_path = _get_file_path(base, sym, check_date)
        if os.path.exists(check_path):
            try:
                with open(check_path, "r") as f:
                    entries = json.load(f)
                if entries:
                    return entries[-1]
            except (json.JSONDecodeError, TypeError):
                continue
    return None


def load_history(sym, days=5, mode="paper"):
    results = []
    base = market_data_dir(mode)
    today = date.today()
    days_checked = 0
    days_found = 0
    d = today
    while days_found < days and days_checked < 10:
        path = _get_file_path(base, sym, d)
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    entries = json.load(f)
                if entries:
                    results.append(entries[-1])
                    days_found += 1
            except (json.JSONDecodeError, TypeError):
                pass
        days_checked += 1
        d -= timedelta(days=1)
    return results


def load_today_snapshots(sym, mode="paper"):
    """Load all snapshots from today."""
    today = date.today()
    path = _get_file_path(market_data_dir(mode), sym, today)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, TypeError):
        return []


# ── Trading data storage (data/{mode}-trading/) ─────────────────────────────

def data_dir(mode):
    """Return the local data directory for a trading mode."""
    d = os.path.join(BASE_DIR, f"{mode}-trading")
    os.makedirs(d, exist_ok=True)
    return d


def load_reasons(mode):
    """Load the order-ID-to-reason mapping."""
    path = os.path.join(data_dir(mode), "reasons.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def save_reasons(mode, reasons):
    """Save the order-ID-to-reason mapping."""
    path = os.path.join(data_dir(mode), "reasons.json")
    with open(path, "w") as f:
        json.dump(reasons, f, indent=2)


def load_known_positions(mode):
    """Load the known positions tracker.

    Each OCC symbol maps to a list of entry dicts (supports multiple buys
    of the same contract).  Transparently migrates the legacy single-dict
    format on read.
    """
    path = os.path.join(data_dir(mode), "known_positions.json")
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        # Migrate legacy format: {occ: {…}} → {occ: [{…}]}
        migrated = False
        for sym, val in data.items():
            if isinstance(val, dict):
                data[sym] = [val]
                migrated = True
        if migrated:
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        return data
    return {}


def save_known_positions(mode, positions):
    """Save the known positions tracker."""
    path = os.path.join(data_dir(mode), "known_positions.json")
    with open(path, "w") as f:
        json.dump(positions, f, indent=2)


def log_event(mode, event_data):
    """Append a structured event to the log."""
    path = os.path.join(data_dir(mode), "log.jsonl")
    event_data["ts"] = datetime.now(ET).isoformat()
    with open(path, "a") as f:
        f.write(json.dumps(event_data) + "\n")


# ── Position snapshot storage (data/{mode}-trading/position-snapshots/) ──────

def save_position_snapshot(mode, symbol, snapshot):
    """Append a position snapshot to the JSONL file for hindsight analysis.

    Records the option's price, IV, greeks, and P&L at each evaluation cycle.
    One file per position (OCC symbol), append-only.
    """
    d = os.path.join(data_dir(mode), "position-snapshots")
    os.makedirs(d, exist_ok=True)
    snapshot["ts"] = datetime.now(ET).isoformat()
    path = os.path.join(d, f"{symbol}.jsonl")
    with open(path, "a") as f:
        f.write(json.dumps(snapshot) + "\n")


def load_position_snapshots(mode, symbol):
    """Load all snapshots for a position from its JSONL file."""
    path = os.path.join(data_dir(mode), "position-snapshots", f"{symbol}.jsonl")
    if not os.path.exists(path):
        return []
    snapshots = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    snapshots.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return snapshots


def count_position_snapshots(mode, symbol):
    """Count snapshots for a position without parsing the full file."""
    path = os.path.join(data_dir(mode), "position-snapshots", f"{symbol}.jsonl")
    if not os.path.exists(path):
        return 0
    count = 0
    with open(path) as f:
        for line in f:
            if line.strip():
                count += 1
    return count


# ── Market snapshot storage (data/{mode}/{TICKER}/iv/) ───────────────────────
# Named "iv" for backward compatibility with existing data directories.

def market_snapshot_dir(ticker, mode="paper"):
    """Return the market snapshot directory for a ticker within a mode."""
    d = os.path.join(market_data_dir(mode), ticker.upper(), "iv")
    os.makedirs(d, exist_ok=True)
    return d


def save_market_snapshot(ticker, price, avg_call_iv, avg_put_iv,
                         avg_call_greeks=None, avg_put_greeks=None,
                         mode="paper"):
    """Save a market data point for a ticker. One file per day.

    Stores stock price, call/put IV, and average near-money Greeks.
    """
    if not avg_call_iv and not avg_put_iv:
        return
    today = date.today().isoformat()
    path = os.path.join(market_snapshot_dir(ticker, mode), f"{today}.json")
    snapshots = []
    if os.path.exists(path):
        try:
            with open(path) as f:
                snapshots = json.load(f)
        except (json.JSONDecodeError, TypeError):
            snapshots = []
    entry = {
        "ts": datetime.now(ET).isoformat(),
        "price": price,
        "avg_call_iv": avg_call_iv,
        "avg_put_iv": avg_put_iv,
    }
    if avg_call_greeks:
        entry["avg_call_greeks"] = avg_call_greeks
    if avg_put_greeks:
        entry["avg_put_greeks"] = avg_put_greeks
    snapshots.append(entry)
    with open(path, "w") as f:
        json.dump(snapshots, f, indent=2)


def load_market_history(ticker, days=7, mode="paper"):
    """Load recent market snapshots for a ticker.

    Returns list of dicts (most recent first) with date, price, IV, and Greeks.
    Uses the last snapshot of each day.
    """
    snap_dir = market_snapshot_dir(ticker, mode)
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    history = []
    if not os.path.isdir(snap_dir):
        return history
    for fname in sorted(os.listdir(snap_dir), reverse=True):
        if not fname.endswith(".json"):
            continue
        day_str = fname.replace(".json", "")
        if day_str < cutoff:
            continue
        path = os.path.join(snap_dir, fname)
        try:
            with open(path) as f:
                snapshots = json.load(f)
            if snapshots:
                last = snapshots[-1]
                entry = {
                    "date": day_str,
                    "price": last.get("price"),
                    "avg_call_iv": last.get("avg_call_iv"),
                    "avg_put_iv": last.get("avg_put_iv"),
                }
                if last.get("avg_call_greeks"):
                    entry["avg_call_greeks"] = last["avg_call_greeks"]
                if last.get("avg_put_greeks"):
                    entry["avg_put_greeks"] = last["avg_put_greeks"]
                history.append(entry)
        except Exception:
            continue
    return history


def load_iv_history(ticker, days=365, mode="paper"):
    """Load IV history for a ticker.

    Returns list of (date, call_iv, put_iv) tuples. Falls back to avg_iv
    for backward compatibility with old snapshot files.
    """
    snap_dir = market_snapshot_dir(ticker, mode)
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    history = []
    if not os.path.isdir(snap_dir):
        return history
    for fname in sorted(os.listdir(snap_dir)):
        if not fname.endswith(".json"):
            continue
        day_str = fname.replace(".json", "")
        if day_str < cutoff:
            continue
        path = os.path.join(snap_dir, fname)
        try:
            with open(path) as f:
                snapshots = json.load(f)
            if snapshots:
                last = snapshots[-1]
                call_iv = last.get("avg_call_iv")
                put_iv = last.get("avg_put_iv")
                if call_iv or put_iv:
                    history.append((day_str, call_iv or 0, put_iv or 0))
                elif last.get("avg_iv"):
                    # Backward compat: old files only have avg_iv
                    iv = last["avg_iv"]
                    history.append((day_str, iv, iv))
        except Exception:
            continue
    return history


# ── News snapshot storage (data/{mode}/{TICKER}/news/) ───────────────────────

def save_news_snapshot(mode, ticker, headlines):
    """Save news headlines for a ticker. One file per day, appends snapshots."""
    ticker = ticker.upper()
    d = os.path.join(market_data_dir(mode), ticker, "news")
    os.makedirs(d, exist_ok=True)
    today = date.today().isoformat()
    path = os.path.join(d, f"{today}.json")
    snapshots = []
    if os.path.exists(path):
        try:
            with open(path) as f:
                snapshots = json.load(f)
        except (json.JSONDecodeError, TypeError):
            snapshots = []
    snapshots.append({
        "ts": datetime.now(ET).isoformat(),
        "headlines": headlines,
    })
    with open(path, "w") as f:
        json.dump(snapshots, f, indent=2)



def load_pending_experience_updates(mode):
    """Load pending experience updates waiting to be processed."""
    path = os.path.join(data_dir(mode), "pending_experience_updates.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []


def save_pending_experience_updates(mode, updates):
    """Persist recently closed positions for the reflect skill.

    Merges with any existing pending updates, deduplicating by symbol.
    """
    existing = load_pending_experience_updates(mode)
    existing_symbols = {item["symbol"] for item in existing}
    for item in updates:
        if item["symbol"] not in existing_symbols:
            existing.append(item)
            existing_symbols.add(item["symbol"])
    path = os.path.join(data_dir(mode), "pending_experience_updates.json")
    with open(path, "w") as f:
        json.dump(existing, f, indent=2)


def clear_pending_experience_updates(mode):
    """Clear pending experience updates after successful processing."""
    path = os.path.join(data_dir(mode), "pending_experience_updates.json")
    if os.path.exists(path):
        os.remove(path)


def load_news_history(mode, ticker, days=7):
    """Load recent news history for a ticker.

    Returns list of dicts with date and headlines, most recent first.
    """
    ticker = ticker.upper()
    news_dir = os.path.join(market_data_dir(mode), ticker, "news")
    if not os.path.isdir(news_dir):
        return []
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    history = []
    for fname in sorted(os.listdir(news_dir), reverse=True):
        if not fname.endswith(".json"):
            continue
        day_str = fname.replace(".json", "")
        if day_str < cutoff:
            continue
        path = os.path.join(news_dir, fname)
        try:
            with open(path) as f:
                snapshots = json.load(f)
            if snapshots:
                last = snapshots[-1]
                history.append({
                    "date": day_str,
                    "headlines": last.get("headlines", []),
                })
        except Exception:
            continue
    return history
