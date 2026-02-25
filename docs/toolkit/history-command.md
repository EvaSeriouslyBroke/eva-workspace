# History Command

The `history` subcommand reads stored historical data and displays recent IV trends for a ticker.

---

## Usage

```
python3 toolkit.py history --ticker <SYM> [--days <N>] [--json]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--days` | 5 | Number of trading days to look back |

---

## What It Reads

This command does NOT call yfinance. It reads from the local data store:

```
~/.openclaw/workspace/options-toolkit/data/{TICKER}/
```

It traverses week folders and daily JSON files to find recent snapshots.

---

## How It Traverses History

1. Start with today's date
2. Compute the week folder: `{YYYY}-W{WW}` (ISO 8601)
3. Check if `data/{TICKER}/{week}/{date}.json` exists
4. If yes, load all snapshots from that file
5. Step back one day, repeat
6. When crossing a week boundary, compute the new week folder
7. Stop after finding `--days` trading days with data, or after checking 10 calendar days (whichever comes first)

### Week Boundary Example

```
Looking for 5 trading days on 2026-02-20 (Thursday, W08):

Day 1: 2026-02-20 → data/IWM/2026-W08/2026-02-20.json ✓
Day 2: 2026-02-19 → data/IWM/2026-W08/2026-02-19.json ✓
Day 3: 2026-02-18 → data/IWM/2026-W08/2026-02-18.json ✓
Day 4: 2026-02-17 → data/IWM/2026-W08/2026-02-17.json ✓
Skip:  2026-02-16 (Sunday) → no file, skip
Skip:  2026-02-15 (Saturday) → no file, skip
Day 5: 2026-02-14 → data/IWM/2026-W07/2026-02-14.json ✓  ← crossed week boundary
```

---

## Formatted Output

A table showing one row per trading day (using the last snapshot of each day):

```
📊 IV HISTORY - IWM (Last 5 Trading Days)
──────────────────────────────────────────────────────────────────────────────────────────

Date          Price      Avg IV     Call IV    Put IV     P/C Vol    P/C OI     Skew
2026-02-20    $210.45    25.30%     24.50%     26.10%     1.05       0.92       +1.60%
2026-02-19    $209.80    25.10%     24.20%     26.00%     1.12       0.95       +1.80%
2026-02-18    $211.20    24.80%     23.90%     25.70%     0.98       0.88       +1.80%
2026-02-17    $210.90    25.50%     24.80%     26.20%     1.08       0.91       +1.40%
2026-02-14    $209.50    26.10%     25.30%     26.90%     1.15       0.97       +1.60%

Trend: IV ↓ CONTRACTING (-0.80% over 5 days)
```

### Trend Line

Compares the oldest and newest day's overall average IV:

| Condition | Display |
|-----------|---------|
| Change > +2% | `IV ↑ EXPANDING (+X.XX% over N days)` 🔴 |
| Change < -2% | `IV ↓ CONTRACTING (-X.XX% over N days)` 🟢 |
| Between -2% and +2% | `IV → STABLE (X.XX% over N days)` 🟡 |

---

## Multiple Snapshots Per Day

Each daily file contains an array of all snapshots from that day (one per cron run, up to ~39). The history command uses only the **last snapshot of each day** for the table — this represents the end-of-day state.

If `--json` is used, all snapshots are returned.

---

## JSON Mode Output

Returns all snapshots (not just last-per-day) within the date range:

```json
{
  "ticker": "IWM",
  "days_requested": 5,
  "days_found": 5,
  "snapshots": [
    {
      "timestamp": "2026-02-20T16:00:00-05:00",
      "price": 210.45,
      "avg_call_iv": 24.50,
      "avg_put_iv": 26.10,
      "overall_avg_iv": 25.30,
      "pc_vol_ratio": 1.05,
      "pc_oi_ratio": 0.92,
      "skew": 1.60
    }
  ],
  "trend": {
    "direction": "CONTRACTING",
    "change": -0.80,
    "period_days": 5
  }
}
```

---

## Error Cases

| Scenario | Behavior |
|----------|----------|
| No data directory for ticker | "No history data found for {SYM}", exit 0 |
| Data exists but fewer days than requested | Shows available days, notes "X of Y days found" |
| Empty data files | Skipped (treated as no data for that day) |
| Corrupted JSON | stderr warning, skip file, continue |

---

## No Market Hours Check

This command reads local files, not live data. It works anytime.
