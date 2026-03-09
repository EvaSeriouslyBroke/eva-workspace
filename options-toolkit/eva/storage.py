"""All file persistence — snapshots, reasons, positions, log, IV."""

import json
import os
from datetime import date, datetime, timedelta

from eva import BASE_DIR, ET


# ── Report snapshot storage (data/{TICKER}/{YYYY}-W{WW}/{date}.json) ─────────

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
    today_path = _get_file_path(base_dir, sym, today)
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
                    results.append(entries[-1])
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
    """Load the known positions tracker."""
    path = os.path.join(data_dir(mode), "known_positions.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
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


# ── IV snapshot storage (data/{TICKER}/iv/) ──────────────────────────────────

def iv_snapshot_dir(ticker):
    """Return the IV snapshot directory for a ticker."""
    d = os.path.join(BASE_DIR, ticker.upper(), "iv")
    os.makedirs(d, exist_ok=True)
    return d


def save_iv_snapshot(ticker, avg_call_iv, avg_put_iv):
    """Save an IV data point for a ticker. One file per day."""
    if not avg_call_iv and not avg_put_iv:
        return
    today = date.today().isoformat()
    path = os.path.join(iv_snapshot_dir(ticker), f"{today}.json")
    snapshots = []
    if os.path.exists(path):
        with open(path) as f:
            snapshots = json.load(f)
    snapshots.append({
        "ts": datetime.now(ET).isoformat(),
        "avg_call_iv": avg_call_iv,
        "avg_put_iv": avg_put_iv,
        "avg_iv": round(((avg_call_iv or 0) + (avg_put_iv or 0)) / 2, 1) if (avg_call_iv or avg_put_iv) else None,
    })
    with open(path, "w") as f:
        json.dump(snapshots, f, indent=2)


def load_iv_history(ticker, days=365):
    """Load IV history for a ticker. Returns list of (date, avg_iv) tuples."""
    snap_dir = iv_snapshot_dir(ticker)
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
                iv = last.get("avg_iv")
                if iv:
                    history.append((day_str, iv))
        except Exception:
            continue
    return history
