# Report Command

The `report` subcommand generates a facts-only options data report. It fetches price and options chain from Tradier, computes IV metrics, then outputs formatted text with `---SPLIT---` markers for Discord delivery.

---

## Usage

```
python3 eva.py report --ticker <SYM> [--force] [--json]
```

| Flag | Description |
|------|-------------|
| `--force` | Skip schedule check (always passed by skills for interactive use) |

---

## Report Generation Flow

### Step 1: Schedule Check

```
if not --force:
    check current time in America/New_York timezone
    if (hour, minute) not in SCHEDULE [(9,31), (11,0), (12,30), (14,0), (15,0), (15,59)]:
        exit 0 with no output (silent skip)
    if weekend (Saturday/Sunday):
        exit 0 with no output (silent skip)
```

### Step 2: Fetch Options Chain (includes price)

```python
from eva.tradier import fetch_options_chain, load_config

cfg = load_config("paper")
chain_data = fetch_options_chain(cfg, sym)
# Internally calls:
#   GET /markets/quotes?symbols={sym}          (price)
#   GET /markets/options/expirations?symbol={sym}  (expirations)
#   GET /markets/options/chains?symbol={sym}&expiration={exp}&greeks=true  (chain)
```

`fetch_options_chain` returns 10 strikes nearest the current price, with calls and puts.

### Step 3: Select Display Strikes

```python
# Report selects the 5 strikes closest to current price from the 10 fetched
report_strikes = sorted(all_call_strikes, key=lambda s: (abs(s - round(price)), -s))[:5]
```

All 10 strikes are saved to the snapshot. Only 5 are displayed.

### Step 4: Load Previous Run

```python
previous = load_previous(sym)
# Returns the most recent snapshot from history, or None if first run
# See data/comparison-logic.md for the lookup algorithm
```

### Step 5: Compute Derived Values

All values computed from raw data and previous run:

| Value | Formula |
|-------|---------|
| avg_call_iv | Mean of 5 displayed call IVs |
| avg_put_iv | Mean of 5 displayed put IVs |
| overall_avg_iv | `(avg_call_iv + avg_put_iv) / 2` |
| skew | `avg_put_iv - avg_call_iv` |
| total_call_vol | Sum of 5 call volumes |
| total_put_vol | Sum of 5 put volumes |
| pc_vol_ratio | `total_put_vol / total_call_vol` (handle div-by-zero) |
| total_call_oi | Sum of 5 call open interests |
| total_put_oi | Sum of 5 put open interests |
| pc_oi_ratio | `total_put_oi / total_call_oi` (handle div-by-zero) |

**If previous run exists**, also compute:

| Value | Formula |
|-------|---------|
| iv_change (per strike) | `current_iv - previous_iv` for matching strikes |
| iv_change_pct (per strike) | `((current_iv - previous_iv) / previous_iv) * 100` |
| avg_call_iv_change | `current_avg_call_iv - previous_avg_call_iv` |
| avg_put_iv_change | `current_avg_put_iv - previous_avg_put_iv` |
| overall_iv_change | `current_overall_iv - previous_overall_iv` |
| pc_vol_change | `current_pc_vol_ratio - previous_pc_vol_ratio` |
| pc_oi_change | `current_pc_oi_ratio - previous_pc_oi_ratio` |
| skew_change | `current_skew - previous_skew` |

### Step 6: Generate Report Chunks

Generate 3 chunks separated by `---SPLIT---` markers:

```
[Chunk 1: History check + Header + Price]
---SPLIT---
[Chunk 2: Options chain tables (calls + puts)]
---SPLIT---
[Chunk 3: IV Summary + Footer + Save confirmation]
```

### Step 7: Save Current Run to History

```python
snapshot = {
    "timestamp": current_time_iso,
    "price": price,
    "prev_close": prev_close,
    "expiry": best_expiry,
    "avg_call_iv": avg_call_iv,
    "avg_put_iv": avg_put_iv,
    "overall_avg_iv": overall_avg_iv,
    "pc_vol_ratio": pc_vol_ratio,
    "pc_oi_ratio": pc_oi_ratio,
    "skew": skew,
    "strikes": { ... }  # Per-strike IVs and volumes (all 10 fetched strikes)
}
save_snapshot(sym, snapshot)
```

### Step 8: Output

Print the complete report to stdout. The `---SPLIT---` markers are part of the output.

---

## The `--force` Flag

| Context | `--force` | Schedule check |
|---------|-----------|----------------|
| Cron (run_all.sh) | Not passed | Active — silent exit outside scheduled times |
| Interactive (skill) | Always passed | Bypassed — always generates report |
| Manual CLI test | Optional | User's choice |

---

## Dynamic Ticker Name

The report header uses the ticker symbol dynamically, not hardcoded to "IWM":

```
  🎯 {TICKER} OPTIONS TRADING ANALYZER
```

---

## JSON Mode Output

When `--json` is passed, outputs a single JSON object containing all computed values. JSON mode includes `directional_score` and `recommendation` fields for programmatic consumption — these do not appear in the formatted text report:

```json
{
  "ticker": "IWM",
  "timestamp": "2026-02-20T10:30:00-05:00",
  "price": { "current": 210.45, "prev_close": 209.80, "change": 0.65, "change_pct": 0.31 },
  "expiry": { "date": "2026-05-16", "dte": 85 },
  "atm_strike": 210,
  "calls": [ ... ],
  "puts": [ ... ],
  "iv_summary": {
    "avg_call_iv": 24.50,
    "avg_put_iv": 26.10,
    "overall_avg_iv": 25.30,
    "skew": 1.60
  },
  "volumes": { "total_call": 9678, "total_put": 8234, "pc_ratio": 0.85 },
  "oi": { "total_call": 54812, "total_put": 47890, "pc_ratio": 0.87 },
  "directional_score": { "bullish": 6, "bearish": 4 },
  "recommendation": "BUY CALLS",
  "previous_run": { "timestamp": "...", "overall_avg_iv": 25.10 }
}
```

---

## Error Cases

| Scenario | Behavior |
|----------|----------|
| Invalid ticker | stderr message, exit 1 |
| No options available | stderr message, exit 1 |
| Tradier API network error | stderr message, exit 1 |
| No previous run data | First-run mode — changes show "N/A", history check shows "first run" |
| Corrupted history file | Warning to stderr, treat as first run |
| Division by zero (zero volume) | P/C ratio shows "N/A" |
