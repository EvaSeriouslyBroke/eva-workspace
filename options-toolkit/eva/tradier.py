"""Tradier API client — config, HTTP helpers, all data fetchers."""

import json
import os
import sys
import time
from datetime import date, datetime, timedelta

import requests

from eva import CONFIG_PATH, ET
from eva.symbols import select_expiry, select_strikes


# ── Config ───────────────────────────────────────────────────────────────────

def load_config(mode):
    """Load Tradier credentials for the given mode."""
    if mode == "real":
        print("Error: real trading is not implemented yet.", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(CONFIG_PATH):
        print(f"Error: config not found at {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    if mode not in cfg:
        print(f"Error: mode '{mode}' not found in tradier.json", file=sys.stderr)
        sys.exit(1)
    section = cfg[mode]
    for key in ("token", "account_id", "base_url"):
        if not section.get(key) or section[key].startswith("<"):
            print(f"Error: '{key}' not configured for mode '{mode}'", file=sys.stderr)
            sys.exit(1)
    return section


# ── HTTP helpers ─────────────────────────────────────────────────────────────

def tradier_get(cfg, path, params=None):
    """GET request to Tradier with retry."""
    url = cfg["base_url"] + path
    headers = {
        "Authorization": f"Bearer {cfg['token']}",
        "Accept": "application/json",
    }
    last_err = None
    for attempt in range(3):
        if attempt > 0:
            time.sleep(2 ** attempt)
        try:
            r = requests.get(url, headers=headers, params=params, timeout=10)
            if r.status_code == 200:
                return r.json()
            last_err = f"HTTP {r.status_code}: {r.text[:200]}"
        except requests.RequestException as e:
            last_err = str(e)
    raise RuntimeError(f"Tradier GET {path} failed after 3 attempts: {last_err}")


def tradier_post(cfg, path, data=None):
    """POST request to Tradier (form-encoded) with retry."""
    url = cfg["base_url"] + path
    headers = {
        "Authorization": f"Bearer {cfg['token']}",
        "Accept": "application/json",
    }
    last_err = None
    for attempt in range(3):
        if attempt > 0:
            time.sleep(2 ** attempt)
        try:
            r = requests.post(url, headers=headers, data=data, timeout=10)
            if r.status_code in (200, 201):
                return r.json()
            last_err = f"HTTP {r.status_code}: {r.text[:200]}"
        except requests.RequestException as e:
            last_err = str(e)
    raise RuntimeError(f"Tradier POST {path} failed after 3 attempts: {last_err}")


def tradier_delete(cfg, path):
    """DELETE request to Tradier with retry."""
    url = cfg["base_url"] + path
    headers = {
        "Authorization": f"Bearer {cfg['token']}",
        "Accept": "application/json",
    }
    last_err = None
    for attempt in range(3):
        if attempt > 0:
            time.sleep(2 ** attempt)
        try:
            r = requests.delete(url, headers=headers, timeout=10)
            if r.status_code in (200, 201):
                return r.json()
            last_err = f"HTTP {r.status_code}: {r.text[:200]}"
        except requests.RequestException as e:
            last_err = str(e)
    raise RuntimeError(f"Tradier DELETE {path} failed after 3 attempts: {last_err}")


def normalize_list(val):
    """Tradier returns 'null' string, None, dict (single item), or list. Always return list."""
    if val is None or val == "null":
        return []
    if isinstance(val, dict):
        return [val]
    if isinstance(val, list):
        return val
    return []


# ── Market status ────────────────────────────────────────────────────────────

def is_market_open(cfg):
    """Check Tradier /markets/clock for actual market state."""
    try:
        resp = tradier_get(cfg, "/markets/clock")
        state = resp.get("clock", {}).get("state", "")
        return state == "open"
    except Exception:
        now = datetime.now(ET)
        if now.weekday() >= 5:
            return False
        from datetime import time as dt_time
        return dt_time(9, 30) <= now.time() <= dt_time(16, 0)


# ── Account data fetchers ───────────────────────────────────────────────────

def fetch_balances(cfg):
    """Fetch account balances."""
    resp = tradier_get(cfg, f"/accounts/{cfg['account_id']}/balances")
    b = resp.get("balances", {})
    cash_info = b.get("cash", {})
    unsettled = cash_info.get("unsettled_funds", 0) or 0
    total_cash = b.get("total_cash", 0) or 0
    settled = total_cash - unsettled if unsettled else total_cash
    return {
        "cash": total_cash,
        "unsettled_funds": unsettled,
        "settled_cash": settled,
        "market_value": b.get("market_value", 0) or 0,
        "total_equity": b.get("total_equity", 0) or 0,
    }


def fetch_positions(cfg):
    """Fetch open positions."""
    resp = tradier_get(cfg, f"/accounts/{cfg['account_id']}/positions")
    positions = resp.get("positions", {})
    if positions == "null" or positions is None:
        return []
    items = positions.get("position", [])
    return normalize_list(items)


def fetch_orders(cfg, limit=50):
    """Fetch recent orders."""
    resp = tradier_get(cfg, f"/accounts/{cfg['account_id']}/orders")
    orders = resp.get("orders", {})
    if orders == "null" or orders is None:
        return []
    items = orders.get("order", [])
    return normalize_list(items)[:limit]


# ── Market data fetchers ────────────────────────────────────────────────────

def fetch_quote(cfg, symbol):
    """Fetch a stock quote (raw Tradier response)."""
    resp = tradier_get(cfg, "/markets/quotes", {"symbols": symbol})
    quotes = resp.get("quotes", {})
    q = quotes.get("quote", {})
    if isinstance(q, list):
        q = q[0] if q else {}
    return q


def fetch_price(cfg, symbol):
    """Fetch current price data, matching the toolkit output format."""
    q = fetch_quote(cfg, symbol)
    price = q.get("last") or q.get("close") or 0
    prev_close = q.get("prevclose") or q.get("close") or 0
    change = q.get("change") or (price - prev_close if price and prev_close else 0)
    change_pct_raw = q.get("change_percentage")
    if change_pct_raw is not None:
        change_pct = float(str(change_pct_raw).replace("%", ""))
    elif prev_close:
        change_pct = (change / prev_close) * 100
    else:
        change_pct = 0
    now = datetime.now(ET)
    return {
        "ticker": symbol,
        "price": price,
        "previous_close": prev_close,
        "change": change,
        "change_pct": change_pct,
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp_iso": now.isoformat(),
    }


def fetch_history(cfg, symbol, days=365):
    """Fetch daily price history."""
    end = date.today()
    start = end - timedelta(days=days)
    resp = tradier_get(cfg, "/markets/history", {
        "symbol": symbol,
        "interval": "daily",
        "start": start.isoformat(),
        "end": end.isoformat(),
    })
    history = resp.get("history", {})
    if history is None or history == "null":
        return []
    days_data = history.get("day", [])
    return normalize_list(days_data)


def fetch_expirations(cfg, symbol):
    """Fetch available option expiration dates."""
    resp = tradier_get(cfg, "/markets/options/expirations", {"symbol": symbol})
    exps = resp.get("expirations", {})
    if exps is None or exps == "null":
        return []
    dates = exps.get("date", [])
    return normalize_list(dates)


def fetch_chain_raw(cfg, symbol, expiration):
    """Fetch raw option chain for a given expiration with greeks."""
    resp = tradier_get(cfg, "/markets/options/chains", {
        "symbol": symbol,
        "expiration": expiration,
        "greeks": "true",
    })
    options = resp.get("options", {})
    if options is None or options == "null":
        return []
    items = options.get("option", [])
    return normalize_list(items)


def fetch_options_chain(cfg, symbol, target_dte=120):
    """Fetch structured options chain data, matching the toolkit output format.

    Replaces the old yfinance-based fetch_chain from toolkit.py.
    Returns dict with calls, puts, price data, expiry info.
    """
    expirations = fetch_expirations(cfg, symbol)
    if not expirations:
        print(f"No options data available for {symbol}", file=sys.stderr)
        sys.exit(1)

    best_expiry = select_expiry(expirations, target_dte)
    dte = (date.fromisoformat(best_expiry) - date.today()).days

    price_data = fetch_price(cfg, symbol)
    price = price_data["price"]
    atm = round(price)

    raw_chain = fetch_chain_raw(cfg, symbol, best_expiry)

    # Collect all strikes from the chain
    all_strikes = sorted(set(opt.get("strike", 0) for opt in raw_chain))
    selected_strikes = select_strikes(all_strikes, price, count=10)

    def _get_iv(opt):
        greeks = opt.get("greeks") or {}
        iv = greeks.get("mid_iv") or greeks.get("smv_vol") or 0
        return round(float(iv) * 100, 2) if iv else 0

    calls = []
    puts = []
    for s in selected_strikes:
        for opt in raw_chain:
            if opt.get("strike") != s:
                continue
            entry = {
                "strike": int(s) if s == int(s) else s,
                "iv": _get_iv(opt),
                "bid": round(float(opt.get("bid", 0) or 0), 2),
                "ask": round(float(opt.get("ask", 0) or 0), 2),
                "last": round(float(opt.get("last", 0) or 0), 2),
                "volume": int(opt.get("volume", 0) or 0),
                "open_interest": int(opt.get("open_interest", 0) or 0),
            }
            if opt.get("option_type") == "call":
                entry["status"] = "ATM" if int(s) == atm else ("ITM" if s < price else "OTM")
                calls.append(entry)
            elif opt.get("option_type") == "put":
                entry["status"] = "ATM" if int(s) == atm else ("ITM" if s > price else "OTM")
                puts.append(entry)

    return {
        "ticker": symbol,
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
