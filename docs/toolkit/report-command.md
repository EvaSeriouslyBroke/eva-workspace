# Report Command

The `report` subcommand generates a facts-only options data report. It fetches price, news, options chain, and IV metrics, then outputs formatted text with `---SPLIT---` markers for Discord delivery.

---

## Usage

```
python3 toolkit.py report --ticker <SYM> [--force] [--json]
```

| Flag | Description |
|------|-------------|
| `--force` | Skip market hours check (always passed by skills for interactive use) |

---

## Report Generation Flow

### Step 1: Market Hours Check

```
if not --force:
    check current time in America/New_York timezone
    if not (Monday-Friday AND 9:30 AM - 4:00 PM ET):
        exit 0 with no output (silent skip)
```

### Step 2: Fetch Price Data

```python
ticker = yf.Ticker(sym)
price = ticker.fast_info['lastPrice']
prev_close = ticker.fast_info['previousClose']
change = price - prev_close
change_pct = (change / prev_close) * 100
```

### Step 3: Fetch Options Chain

```python
expirations = ticker.options
best_expiry = select_expiry(expirations, target_dte=120)
chain = ticker.option_chain(best_expiry)

atm_strike = round(price)
strikes = select_strikes(chain, price)  # 5 strikes nearest ATM
```

For each of the 5 strikes, extract from both `chain.calls` and `chain.puts`:
- strike, impliedVolatility, bid, ask, lastPrice, volume, openInterest

### Step 4: Fetch News

```python
articles = ticker.news  # Up to 8 recent headlines
sentiment_score = score_sentiment(articles)
themes = detect_themes(articles)
```

### Step 5: Load Previous Run

```python
previous = load_previous(sym)
# Returns the most recent snapshot from history, or None if first run
# See data/comparison-logic.md for the lookup algorithm
```

### Step 6: Compute Derived Values

All values computed from raw data and previous run:

| Value | Formula |
|-------|---------|
| avg_call_iv | Mean of 5 call IVs |
| avg_put_iv | Mean of 5 put IVs |
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

### Step 7: Generate Each Section

Generate all 8 sections in order. See `output-format/` docs for exact formatting rules per section. Insert `---SPLIT---` markers between section groups:

```
[Section 1: History check]
[Section 2: Main header]
[Section 3: Price & metadata]
[Section 4: News headlines]
---SPLIT---
[Section 5: Target expiration]
[Section 6: Call options table]
[Section 7: Put options table]
---SPLIT---
[Section 8: IV summary]
[Footer: REPORT COMPLETE]
[Save confirmation]
```

### Step 8: Save Current Run to History

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
    "strikes": { ... }  # Per-strike IVs and volumes
}
save_snapshot(sym, snapshot)
```

### Step 9: Output

Print the complete report to stdout. The `---SPLIT---` markers are part of the output.

---

## The `--force` Flag

| Context | `--force` | Market hours check |
|---------|-----------|-------------------|
| Cron (run_all.sh) | Not passed | Active — silent exit outside 9:30-16:00 ET Mon-Fri |
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
  "news": { "headlines": [...], "sentiment": {...}, "themes": [...] },
  "iv_summary": {
    "avg_call_iv": 24.50,
    "avg_put_iv": 26.10,
    "overall_avg_iv": 25.30,
    "skew": 1.60,
    "changes": { ... }
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
| yfinance network error | stderr message, exit 1 |
| No previous run data | First-run mode — changes show "N/A", Section 1 shows "first run" |
| Corrupted history file | Warning to stderr, treat as first run |
| Division by zero (zero volume) | P/C ratio shows "N/A", sentiment shows "NEUTRAL" |
