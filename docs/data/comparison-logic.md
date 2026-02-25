# Comparison Logic

How the toolkit finds the "previous run" and calculates changes between runs.

---

## Finding the Previous Run

When generating a report, the toolkit needs the most recent previous snapshot to compute IV changes, volume trend shifts, and skew movement. Here's the lookup algorithm:

### Step 1: Check Today's File

```
data/{TICKER}/{current_week}/{today}.json
```

If this file exists and has entries, use the **second-to-last entry** (the last entry before the current run). If only one entry exists (this is the first run today), move to Step 2.

### Step 2: Check Yesterday

Compute yesterday's date. If yesterday is Saturday or Sunday, walk back to Friday.

```
data/{TICKER}/{week_of_yesterday}/{yesterday}.json
```

If this file exists, use the **last entry** in the array.

### Step 3: Walk Backwards

If yesterday's file doesn't exist (holiday, data gap), continue walking backwards day by day:

```
Day -2, Day -3, Day -4, ...
```

For each day:
1. Compute its week folder
2. Check if the daily file exists
3. If yes, use the last entry

Stop after checking 10 calendar days back. If nothing is found within 10 days, enter "first run" mode.

### Step 4: First Run Mode

If no previous data is found:

- Section 1 shows: `ℹ️  No previous IV data found - first run`
- All change columns show `N/A` with 🟡
- Skew change, volume change, OI change all omitted
- Directional scoring still works in JSON mode (uses absolute values, not changes)

---

## Pseudocode

```python
def load_previous(ticker):
    base = f"data/{ticker}"
    today = date.today()

    # Step 1: Today's file
    today_file = get_file_path(base, today)
    if exists(today_file):
        entries = load_json(today_file)
        if len(entries) >= 1:
            return entries[-1]  # Most recent entry from earlier today

    # Steps 2-3: Walk backwards
    for days_back in range(1, 11):
        check_date = today - timedelta(days=days_back)
        check_file = get_file_path(base, check_date)
        if exists(check_file):
            entries = load_json(check_file)
            if entries:
                return entries[-1]

    # Step 4: Nothing found
    return None
```

Note: When the current run is the first entry of the day, Step 1 returns the snapshot from earlier today if multiple runs exist. If it's the very first run of the day, we fall through to Step 2 (yesterday's data).

---

## What Gets Compared

### Aggregate Values

| Current Value | Previous Value | Change Computed |
|---------------|----------------|-----------------|
| avg_call_iv | previous.avg_call_iv | `current - previous` |
| avg_put_iv | previous.avg_put_iv | `current - previous` |
| overall_avg_iv | previous.overall_avg_iv | `current - previous` |
| pc_vol_ratio | previous.pc_vol_ratio | `current - previous` |
| pc_oi_ratio | previous.pc_oi_ratio | `current - previous` |
| skew | previous.skew | `current - previous` |

### Per-Strike Values

For each of the 5 strikes in the current run:
1. Check if the same strike exists in `previous.strikes`
2. If yes: compute `current_iv - previous_iv` for both call and put
3. If no (strike wasn't in previous run): show `N/A`

This handles the case where ATM shifts between runs (e.g., price moves from $210 to $212, so the 5-strike window moves).

---

## Change Calculation Formulas

### Absolute Change

```
change = current_value - previous_value
```

Display: `+X.XX` or `-X.XX` (sign always shown)

### Percentage Change (for per-strike IV)

```
pct_change = ((current_iv - previous_iv) / previous_iv) * 100
```

Display format: `+1.10% (+5.0%)`
- First number: absolute change in percentage points
- Second number (in parens): relative percentage change

### Example

```
Previous call IV at $210 strike: 22.00%
Current call IV at $210 strike:  23.10%

Absolute change: +1.10 percentage points
Relative change: (1.10 / 22.00) * 100 = +5.0%

Display: +1.10% (+5.0%) 🔴
```

---

## Change Color Rules

### IV Changes

| Direction | Emoji | Reason |
|-----------|-------|--------|
| IV increased | 🔴 | Options more expensive |
| IV decreased | 🟢 | Options cheaper |
| No change | 🟡 | Stable |
| N/A | 🟡 | First run |

### Ratio Changes (P/C Volume, P/C OI)

| Direction | Emoji | Reason |
|-----------|-------|--------|
| Ratio increased | 🔴 | More bearish positioning |
| Ratio decreased | 🟢 | More bullish positioning |

### Skew Changes

| Condition | Emoji |
|-----------|-------|
| |change| > 1 | 🔴 |
| |change| <= 1 | 🟡 |

---

## Edge Cases

### Strike Mismatch

If the current price moved significantly since the last run, the 5 selected strikes may not overlap with the previous run's strikes. For non-overlapping strikes:
- IV change shows `N/A`
- This is expected and not an error

### Expiry Change

If the selected expiry changes between runs (e.g., a nearer expiry was removed after it expired), IV comparisons are still made strike-by-strike. The expiry difference is not flagged — IVs at the same strike are comparable even across different (but similar) expirations.

### Weekend Gap

Friday 4:00 PM → Monday 9:30 AM is the normal pattern. The "walk backwards" algorithm handles this: Monday's first run looks at Friday's data. No special weekend logic needed.

### Long Gaps

If the toolkit hasn't run for several days (e.g., server was down), the 10-day lookback handles gaps up to 10 calendar days. Beyond that, it enters first-run mode. This is acceptable — IV comparisons over very long gaps are less meaningful anyway.

### Division by Zero

When computing percentage change, if `previous_iv` is 0 (theoretically possible but rare):
- Show absolute change only
- Skip the relative percentage
- Display: `+X.XX% (N/A)`

When computing P/C ratios, if total call volume or OI is 0:
- Ratio shows `N/A`
- Sentiment shows `NEUTRAL`
