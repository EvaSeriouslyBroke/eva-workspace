# Storage Format

This document specifies the directory layout, file naming conventions, and JSON schemas for the persistent data store.

---

## Directory Structure

```
~/.openclaw/workspace/options-toolkit/data/
  {TICKER}/
    {YYYY}-W{WW}/
      {YYYY-MM-DD}.json
```

### Examples

```
data/
  IWM/
    2026-W07/
      2026-02-10.json
      2026-02-11.json
      2026-02-12.json
      2026-02-13.json
      2026-02-14.json
    2026-W08/
      2026-02-17.json
      2026-02-18.json
      2026-02-19.json
      2026-02-20.json
  SPY/
    2026-W08/
      2026-02-17.json
      ...
  cron.log
```

### Naming Conventions

| Component | Format | Example | Rule |
|-----------|--------|---------|------|
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

## Daily File Format

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
      },
      "209": { ... },
      "210": { ... },
      "211": { ... },
      "212": { ... }
    }
  },
  {
    "timestamp": "2026-02-20T09:40:00-05:00",
    ...
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
| `avg_call_iv` | float | Average IV across 5 call strikes (percentage, e.g., 24.50) |
| `avg_put_iv` | float | Average IV across 5 put strikes (percentage) |
| `overall_avg_iv` | float | `(avg_call_iv + avg_put_iv) / 2` |
| `pc_vol_ratio` | float | Put/call volume ratio |
| `pc_oi_ratio` | float | Put/call open interest ratio |
| `skew` | float | `avg_put_iv - avg_call_iv` (percentage points) |
| `strikes` | object | Per-strike data (keyed by strike price as string) |

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

## File Creation Process

### 1. Determine paths

```python
from datetime import datetime, date
import os, json

ticker = "IWM"
today = date.today()
year, week, _ = today.isocalendar()

base_dir = os.path.expanduser("~/.openclaw/workspace/options-toolkit/data")
week_dir = os.path.join(base_dir, ticker, f"{year}-W{week:02d}")
day_file = os.path.join(week_dir, f"{today.isoformat()}.json")
```

### 2. Create week directory

```python
os.makedirs(week_dir, exist_ok=True)  # mkdir -p equivalent
```

### 3. Load existing or start fresh

```python
if os.path.exists(day_file):
    with open(day_file, 'r') as f:
        snapshots = json.load(f)  # Existing array
else:
    snapshots = []  # New file
```

### 4. Append new snapshot

```python
snapshots.append(new_snapshot)
```

### 5. Write back

```python
with open(day_file, 'w') as f:
    json.dump(snapshots, f, indent=2)
```

---

## Data Retention Policy

**Files are never deleted.** This is intentional — see [design-decisions.md](../architecture/design-decisions.md#why-data-grows-forever).

### Storage Estimates

| Metric | Value |
|--------|-------|
| Snapshot size | ~2 KB (5 strikes, all fields) |
| Runs per day | ~39 (every 10 min, 9:30-16:00 = 39 intervals) |
| Daily file size | ~78 KB |
| Weekly file count | 5 files (Mon-Fri) |
| Weekly total | ~390 KB |
| Annual total (per ticker) | ~20 MB (252 trading days) |
| 10 tickers, 5 years | ~1 GB |

---

## `cron.log`

Location: `data/cron.log`

Contains stderr output from cron runs. Crontab appends both stdout and stderr:

```cron
... run_all.sh >> .../data/cron.log 2>&1
```

In practice, stdout from successful runs goes to Discord via `openclaw message send`, so only errors and the script's own logging end up in cron.log.

Log rotation is not yet implemented. The file will grow indefinitely. A future enhancement could truncate or rotate it.
