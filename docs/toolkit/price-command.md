# Price Command

The `price` subcommand fetches and displays the current stock price with change data.

---

## Usage

```
python3 toolkit.py price --ticker <SYM> [--json]
```

## What It Fetches

| Field | Source | Description |
|-------|--------|-------------|
| Current price | `yf.Ticker(sym).fast_info['lastPrice']` or `.info['currentPrice']` | Latest available price |
| Previous close | `yf.Ticker(sym).fast_info['previousClose']` or `.info['previousClose']` | Prior trading day's close |
| Dollar change | Computed: `price - prev_close` | Absolute change |
| Percent change | Computed: `(dollar_change / prev_close) * 100` | Relative change |

### yfinance API Calls

```python
import yfinance as yf
ticker = yf.Ticker(sym)

# Preferred (faster):
price = ticker.fast_info['lastPrice']
prev_close = ticker.fast_info['previousClose']

# Fallback (slower, more fields):
price = ticker.info['currentPrice']
prev_close = ticker.info['previousClose']
```

`fast_info` is preferred because it makes fewer HTTP requests. Fall back to `info` if `fast_info` doesn't have the needed fields.

---

## Formatted Output

Matches Section 3 of OUTPUT.md:

```
Current IWM Price: $210.45 🟢 (+$0.65 / +0.31%)
Previous Close: $209.80
Analysis Time: 2026-02-20 10:30:00
```

### Color Rules

| Condition | Emoji |
|-----------|-------|
| Price > previous close (positive change) | 🟢 |
| Price < previous close (negative change) | 🔴 |
| Price = previous close (no change) | 🟡 |

### Number Formatting

- Price: `$X.XX` (always 2 decimal places)
- Dollar change: `+$X.XX` or `-$X.XX` (sign always shown)
- Percent change: `+X.XX%` or `-X.XX%` (sign always shown)

---

## JSON Mode Output

```json
{
  "ticker": "IWM",
  "price": 210.45,
  "previous_close": 209.80,
  "change": 0.65,
  "change_pct": 0.31,
  "timestamp": "2026-02-20T10:30:00-05:00"
}
```

---

## Error Cases

| Scenario | Behavior |
|----------|----------|
| Invalid ticker symbol | yfinance raises exception → stderr message, exit code 1 |
| Market closed (weekend/holiday) | Returns last available price (Friday's close). Still works — shows stale timestamp. |
| Network failure | yfinance raises exception → stderr message, exit code 1 |
| yfinance rate limit (429) | yfinance raises exception → stderr message, exit code 1 |

---

## No Market Hours Check

This command does NOT check market hours. It always returns data. During market hours, the price is live. Outside market hours, it shows the most recent closing price. This is intentional — users asking "what's IWM at?" should always get an answer.
