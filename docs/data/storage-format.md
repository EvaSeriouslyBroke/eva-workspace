# Storage Format

This document specifies the directory layout, file naming conventions, and JSON schemas for the persistent data store.

---

## Directory Structure

All market data is stored under a mode prefix (`paper` or `live`) because
Tradier sandbox data is 15-minute delayed vs real-time for live. This prevents
delayed and real-time data from mixing, which would corrupt IV rank calculations
and give paper trading future knowledge of live data.

```
~/.openclaw/workspace/options-toolkit/data/
  {mode}/                          ← "paper" or "live"
    {TICKER}/
      {YYYY}-W{WW}/
        {YYYY-MM-DD}.json          ← Report snapshots
      iv/
        {YYYY-MM-DD}.json          ← IV history
      news/
        {YYYY-MM-DD}.json          ← News headline history
  {mode}-trading/                  ← "paper-trading" or "real-trading"
    reasons.json                   ← Order reasoning
    known_positions.json           ← Position tracker
    log.jsonl                      ← Event log
```

### Examples

```
data/
  paper/
    IWM/
      2026-W07/
        2026-02-10.json
        2026-02-11.json
      iv/
        2026-02-10.json
        2026-02-11.json
      news/
        2026-02-10.json
    SPY/
      2026-W08/
        2026-02-17.json
  paper-trading/
    reasons.json
    known_positions.json
    log.jsonl
  cron.log
```

### Naming Conventions

| Component | Format | Example | Rule |
|-----------|--------|---------|------|
| Mode prefix | Lowercase | `paper`, `live` | Matches `--mode` argument |
| Ticker folder | Uppercase symbol | `IWM`, `SPY` | Matches `--ticker` argument (uppercased) |
| Week folder | `{YYYY}-W{WW}` | `2026-W08` | ISO 8601 week number, zero-padded |
| Daily file | `{YYYY-MM-DD}.json` | `2026-02-20.json` | Calendar date of the run |

### Week Number Calculation

Uses ISO 8601 week numbering:

```python
from datetime import date
d = date(2026, 2, 20)
year, week, _ = d.isocalendar()
folder = f"{year}-W{week:02d}"  # "2026-W08"
```

Note: ISO weeks can cause the year in the week folder to differ from the calendar year in edge cases (e.g., Dec 31 might be W01 of next year). Use `isocalendar()` for both year and week to stay consistent.

---

## Daily File Format (Report Snapshots)

Each daily file is a **JSON array** of snapshot objects. One snapshot is appended per toolkit run during market hours.

```json
[
  {
    "timestamp": "2026-02-20T09:30:00-05:00",
    "price": 210.15,
    "prev_close": 209.80,
    "expiry": "2026-05-16",
    "avg_call_iv": 24.20,
    "avg_put_iv": 25.80,
    "overall_avg_iv": 25.00,
    "pc_vol_ratio": 0.95,
    "pc_oi_ratio": 0.90,
    "skew": 1.60,
    "strikes": {
      "208": {
        "call_iv": 22.50,
        "put_iv": 24.80,
        "call_vol": 450,
        "put_vol": 380,
        "call_oi": 7654,
        "put_oi": 6234
      }
    }
  }
]
```

### Snapshot JSON Schema

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string (ISO 8601) | Time of the run, with timezone offset |
| `price` | float | Current stock price at time of run |
| `prev_close` | float | Previous trading day's closing price |
| `expiry` | string (YYYY-MM-DD) | Selected options expiration date |
| `avg_call_iv` | float | Average IV across displayed call strikes (percentage, e.g., 24.50) |
| `avg_put_iv` | float | Average IV across displayed put strikes (percentage) |
| `overall_avg_iv` | float | `(avg_call_iv + avg_put_iv) / 2` |
| `pc_vol_ratio` | float | Put/call volume ratio |
| `pc_oi_ratio` | float | Put/call open interest ratio |
| `skew` | float | `avg_put_iv - avg_call_iv` (percentage points) |
| `strikes` | object | Per-strike data (keyed by strike price as string). 10 strikes are saved per snapshot. |

### Per-Strike Schema (within `strikes`)

| Field | Type | Description |
|-------|------|-------------|
| `call_iv` | float | Call implied volatility (percentage) |
| `put_iv` | float | Put implied volatility (percentage) |
| `call_vol` | int | Call volume |
| `put_vol` | int | Put volume |
| `call_oi` | int | Call open interest |
| `put_oi` | int | Put open interest |

---

## Market Snapshot History

**Location**: `data/{mode}/{TICKER}/iv/{YYYY-MM-DD}.json`

JSON array of market snapshots saved during each evaluation (one file per day,
multiple entries per day). Directory is named `iv/` for backward compatibility.

```json
[
  {
    "ts": "2026-02-20T09:30:00-05:00",
    "price": 210.15,
    "avg_call_iv": 24.20,
    "avg_put_iv": 25.80,
    "avg_call_greeks": {
      "delta": 0.425,
      "gamma": 0.015,
      "theta": -0.012,
      "vega": 0.18,
      "rho": 0.045
    },
    "avg_put_greeks": {
      "delta": -0.575,
      "gamma": 0.014,
      "theta": -0.011,
      "vega": 0.17,
      "rho": -0.042
    }
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| `ts` | string (ISO 8601) | Timestamp of the evaluation |
| `price` | float | Stock price at evaluation time |
| `avg_call_iv` | float | Average IV of near-money calls (percentage) |
| `avg_put_iv` | float | Average IV of near-money puts (percentage) |
| `avg_call_greeks` | object | Average Greeks of near-money calls (delta, gamma, theta, vega, rho) |
| `avg_put_greeks` | object | Average Greeks of near-money puts |

Used to compute IV rank/percentile (52-week positioning) and for Eva to
reference historical market conditions when recognizing patterns.

---

## News History Format

**Location**: `data/{mode}/{TICKER}/news/{YYYY-MM-DD}.json`

JSON array of news snapshots. Each evaluate cycle fetches fresh headlines from
yfinance and appends a snapshot. Deep news research (`news-research` command)
is done separately only for tickers Eva wants to act on.

```json
[
  {
    "ts": "2026-02-20T09:30:00-05:00",
    "headlines": [
      {
        "title": "IWM Drops on Tariff Concerns",
        "publisher": "Reuters",
        "date": "2026-02-20"
      }
    ]
  }
]
```

Used to correlate past news with price movements without Eva needing
firsthand experience.

---

## File Creation Process

### 1. Determine paths

```python
from datetime import date
import os, json

mode = "paper"
ticker = "IWM"
today = date.today()
year, week, _ = today.isocalendar()

base_dir = os.path.expanduser("~/.openclaw/workspace/options-toolkit/data")
mode_dir = os.path.join(base_dir, mode)
week_dir = os.path.join(mode_dir, ticker, f"{year}-W{week:02d}")
day_file = os.path.join(week_dir, f"{today.isoformat()}.json")
```

### 2. Create directories and write

```python
os.makedirs(week_dir, exist_ok=True)
# Load existing or start fresh, append, write back
```

---

## Data Retention Policy

**Files are never deleted.** This is intentional — see [design-decisions.md](../architecture/design-decisions.md#why-data-grows-forever).

### Storage Estimates

| Metric | Value |
|--------|-------|
| Snapshot size | ~2 KB (10 strikes, all fields) |
| Runs per day | ~6 (6 scheduled report times) |
| Daily file size | ~12 KB |
| Weekly file count | 5 files (Mon-Fri) |
| Weekly total | ~60 KB |
| Annual total (per ticker per mode) | ~3 MB (252 trading days) |

---

## `cron.log`

Location: `data/cron.log`

Contains output from `run_all.sh` — diagnostic messages and errors from `openclaw message send` calls. Crontab appends both stdout and stderr:

```cron
... run_all.sh >> .../data/cron.log 2>&1
```

Log rotation is not yet implemented. The file will grow indefinitely.
