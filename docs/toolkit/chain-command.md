# Chain Command

The `chain` subcommand fetches and displays the options chain for a given ticker, showing calls and puts near the at-the-money strike.

---

## Usage

```
python3 toolkit.py chain --ticker <SYM> [--dte <N>] [--json]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--dte` | 120 | Target days to expiration for expiry selection |

---

## How Expiry Selection Works

1. Fetch all available expirations: `yf.Ticker(sym).options` → list of date strings (e.g., `['2026-03-21', '2026-04-18', '2026-05-16', ...]`)
2. For each expiration, compute DTE: `(expiry_date - today).days`
3. Pick the expiry with DTE closest to the target (default 120)
4. If two expiries are equidistant, pick the later one (more time value)

```python
import yfinance as yf
from datetime import date

ticker = yf.Ticker(sym)
expirations = ticker.options  # List of 'YYYY-MM-DD' strings

today = date.today()
target_dte = 120

best = min(expirations, key=lambda exp: abs((date.fromisoformat(exp) - today).days - target_dte))
```

---

## How ATM Strike Is Determined

```
ATM strike = round(current_price)
```

Current price rounded to the nearest integer. For IWM at $210.45, ATM = $210. For SPY at $503.67, ATM = $504.

---

## Strike Selection

`select_strikes(chain_df, price, count)` picks the `count` strikes closest to the current price, sorted descending.

### Standalone `chain` command

Fetches **5** strikes closest to the current price.

### `report` command

Fetches **10** strikes closest to the current price from yfinance. All 10 are saved to the snapshot for historical IV tracking. The report then selects the **5 closest to the current price** for display. This means if the price moves between runs, the wider 10-strike window still provides previous IV data for comparison.

```
Example for IWM at $210.45 (ATM = $210):

Fetched (10 strikes): $206-$215
Displayed (5 strikes, descending):
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
chain = ticker.option_chain(best_expiry)

calls_df = chain.calls  # pandas DataFrame
puts_df = chain.puts    # pandas DataFrame
```

### Columns Used from DataFrame

| DataFrame Column | Display Column | Format |
|-----------------|----------------|--------|
| `strike` | Strike | `$XXX` |
| `impliedVolatility` | IV | `XX.XX%` (multiply by 100) |
| `bid` | Bid | `$X.XX` |
| `ask` | Ask | `$X.XX` |
| `lastPrice` | Last | `$X.XX` |
| `volume` | Vol | Comma-separated integer |
| `openInterest` | OI | Comma-separated integer |

Note: yfinance returns `impliedVolatility` as a decimal (e.g., 0.2450 for 24.50%). Multiply by 100 for display.

---

## Formatted Output

Matches Sections 5-7 of OUTPUT.md.

### Section 5: Target Expiration Header

```
Target Expiration: 2026-05-16 (85 days)
ATM Strike: $210
```

### Section 6: Call Options Table

```
📈 CALL OPTIONS - Implied Volatility
──────────────────────────────────────────────────────────────────────────────────────────

Strike       IV           IV Chg       Bid        Ask        Last       Vol        OI           Status
$212        🟡 24.50%     N/A         $3.20      $3.45      $3.30      1,245      8,901        OTM 🔵
$211        🟡 23.80%     N/A         $3.85      $4.10      $3.95      2,100      12,345       OTM 🔵
$210        🟡 23.20%     N/A         $4.50      $4.75      $4.60      3,456      15,678       ATM 🟡
$209        🟡 22.90%     N/A         $5.20      $5.45      $5.30      1,890      10,234       ITM 🟢
$208        🟡 22.50%     N/A         $5.90      $6.15      $6.00      987        7,654        ITM 🟢
```

### Section 7: Put Options Table

Same format. Status rules are reversed (see below).

---

## IV Color Rules

| IV Value | Emoji | Meaning |
|----------|-------|---------|
| < 20% | 🟢 | Low / cheap |
| 20% - 35% | 🟡 | Normal |
| > 35% | 🔴 | High / expensive |

---

## IV Change Column

The `chain` command run standalone (not as part of `report`) shows `N/A` for IV change because it doesn't load history. The `report` command populates this column with actual changes.

| Condition | Display | Emoji |
|-----------|---------|-------|
| IV increased from last run | `+X.XX% (+X.X%)` | 🔴 |
| IV decreased from last run | `-X.XX% (-X.X%)` | 🟢 |
| No change | `--` | 🟡 |
| No previous data | `N/A` | 🟡 |

The format `+X.XX% (+X.X%)` shows:
- First: absolute change in IV percentage points
- Second (in parens): relative percentage change

Example: IV was 22.00%, now 23.10% → `+1.10% (+5.0%)`

---

## Status Column Rules

### For Calls

| Condition | Status | Emoji |
|-----------|--------|-------|
| Strike < current price | ITM | 🟢 |
| Strike = ATM strike | ATM | 🟡 |
| Strike > current price | OTM | 🔵 |

### For Puts (Reversed)

| Condition | Status | Emoji |
|-----------|--------|-------|
| Strike > current price | ITM | 🟢 |
| Strike = ATM strike | ATM | 🟡 |
| Strike < current price | OTM | 🔵 |

---

## Table Sorting

Both call and put tables: **5 strikes, sorted descending by strike price** (highest first).

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
| Strike gaps (e.g., $5 increments) | Selects nearest 5 available strikes to ATM |
| Missing volume/OI data | Shows 0 |
| Network failure | stderr message, exit 1 |
