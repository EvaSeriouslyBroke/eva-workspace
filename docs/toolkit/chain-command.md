# Chain Command

The `chain` subcommand fetches and displays the options chain for a given ticker, showing calls and puts near the at-the-money strike.

---

## Usage

```
python3 eva.py chain --ticker <SYM> [--dte <N>] [--json]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--dte` | 120 | Target days to expiration for expiry selection |

---

## How Expiry Selection Works

1. Fetch all available expirations from Tradier: `GET /markets/options/expirations?symbol={sym}`
2. For each expiration, compute DTE: `(expiry_date - today).days`
3. Pick the expiry with DTE closest to the target (default 120)
4. If two expiries are equidistant, pick the later one (more time value)

```python
from eva.tradier import fetch_expirations, load_config
from eva.symbols import select_expiry

cfg = load_config("paper")
expirations = fetch_expirations(cfg, sym)  # List of 'YYYY-MM-DD' strings
best = select_expiry(expirations, target_dte=120)
```

---

## How ATM Strike Is Determined

```
ATM strike = round(current_price)
```

Current price rounded to the nearest integer. For IWM at $210.45, ATM = $210. For SPY at $503.67, ATM = $504.

---

## Strike Selection

`select_strikes(strikes, price, count)` picks the `count` strikes nearest to the current price, sorted descending.

### Standalone `chain` command

Fetches **10** strikes closest to the current price (via `fetch_options_chain` which calls `select_strikes` with `count=10`).

### `report` command

Uses the same `fetch_options_chain` (10 strikes). All 10 are saved to the snapshot for historical IV tracking. The report then selects the **5 closest to the current price** for display. This means if the price moves between runs, the wider 10-strike window still provides previous IV data for comparison.

```
Example for IWM at $210.45 (ATM = $210):

Fetched (10 strikes): $206-$215
Report displays (5 strikes, descending):
  $212  ← 2 above ATM
  $211  ← 1 above ATM
  $210  ← ATM
  $209  ← 1 below ATM
  $208  ← 2 below ATM
```

If strikes don't exist at every $1 increment (some tickers use $2.50 or $5 increments), the nearest available strikes are used.

---

## Fetching the Chain Data

```python
from eva.tradier import fetch_chain_raw, load_config

cfg = load_config("paper")
raw_chain = fetch_chain_raw(cfg, sym, best_expiry)
# Calls: GET /markets/options/chains?symbol={sym}&expiration={exp}&greeks=true
```

### Fields Used from Tradier Response

| Tradier Field | Display Field | Format |
|---------------|---------------|--------|
| `strike` | Strike | `$XXX` |
| `greeks.mid_iv` or `greeks.smv_vol` | IV | `XX.XX%` (multiply by 100) |
| `bid` | Bid | `$X.XX` |
| `ask` | Ask | `$X.XX` |
| `last` | Last | `$X.XX` |
| `volume` | Vol | Comma-separated integer |
| `open_interest` | OI | Comma-separated integer |

Note: Tradier returns IV as a decimal in the greeks (e.g., 0.2450 for 24.50%). Multiply by 100 for display.

---

## Formatted Output

### Target Expiration Header

```
Target Expiration: 2026-05-16 (85 days)
ATM Strike: $210
```

### Call Options — Stacked Cards

The emoji header sits outside the code block so it renders on Discord:

```
📈 CALLS
```

Each strike is a 3-line card inside a code block, separated by blank lines (10 cards total, showing abbreviated example with 3):

~~~
```
$212 OTM | IV: 24.50%
  Chg: N/A | B/A: $3.20/$3.45
  Last: $3.30 | Vol: 1,245 | OI: 8,901

$210 ATM | IV: 23.20%
  Chg: N/A | B/A: $4.50/$4.75
  Last: $4.60 | Vol: 3,456 | OI: 15,678

$208 ITM | IV: 22.50%
  Chg: N/A | B/A: $5.90/$6.15
  Last: $6.00 | Vol: 987 | OI: 7,654
```
~~~

### Put Options — Stacked Cards

```
📉 PUTS
```

Same 3-line card format. Status rules are reversed (see below).

### Card Rules

- **Sorted descending** by strike price (highest first)
- **Line 1**: `$STRIKE STATUS | IV: XX.XX%`
- **Line 2**: `  Chg: {change} | B/A: $bid/$ask`
- **Line 3**: `  Last: $X.XX | Vol: N,NNN | OI: N,NNN`
- No emoji for status inside code blocks (they don't render well)

---

## IV Change Column

The `chain` command run standalone (not as part of `report`) shows `N/A` for IV change because it doesn't load history. The `report` command populates this column with actual changes.

| Condition | Display |
|-----------|---------|
| IV increased from last run | `+X.XX% (+X.X%)` |
| IV decreased from last run | `-X.XX% (-X.X%)` |
| No previous data | `N/A` |

The format `+X.XX% (+X.X%)` shows:
- First: absolute change in IV percentage points
- Second (in parens): relative percentage change

Example: IV was 22.00%, now 23.10% → `+1.10% (+5.0%)`

---

## Status Column Rules

### For Calls

| Condition | Status |
|-----------|--------|
| Strike < current price | ITM |
| Strike = ATM strike | ATM |
| Strike > current price | OTM |

### For Puts (Reversed)

| Condition | Status |
|-----------|--------|
| Strike > current price | ITM |
| Strike = ATM strike | ATM |
| Strike < current price | OTM |

---

## JSON Mode Output

```json
{
  "ticker": "IWM",
  "expiry": "2026-05-16",
  "dte": 85,
  "atm_strike": 210,
  "current_price": 210.45,
  "calls": [
    {
      "strike": 212,
      "iv": 24.50,
      "bid": 3.20,
      "ask": 3.45,
      "last": 3.30,
      "volume": 1245,
      "open_interest": 8901,
      "status": "OTM"
    }
  ],
  "puts": [
    {
      "strike": 212,
      "iv": 26.80,
      "bid": 5.10,
      "ask": 5.35,
      "last": 5.20,
      "volume": 890,
      "open_interest": 6543,
      "status": "ITM"
    }
  ]
}
```

---

## Error Cases

| Scenario | Behavior |
|----------|----------|
| Invalid ticker | stderr message, exit 1 |
| No options available | stderr: "No options data available for {SYM}", exit 1 |
| No expiry near target DTE | Uses closest available (could be far from target) |
| Strike gaps (e.g., $5 increments) | Selects nearest available strikes to ATM |
| Missing volume/OI data | Shows 0 |
| Network failure | stderr message, exit 1 |
