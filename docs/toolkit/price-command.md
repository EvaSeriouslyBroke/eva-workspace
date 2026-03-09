# Price Command

The `price` subcommand fetches and displays the current stock price with change data.

---

## Usage

```
python3 eva.py price --ticker <SYM> [--json]
```

## What It Fetches

| Field | Source | Description |
|-------|--------|-------------|
| Current price | Tradier `quote.last` or `quote.close` | Latest available price |
| Previous close | Tradier `quote.prevclose` or `quote.close` | Prior trading day's close |
| Dollar change | Tradier `quote.change` (or computed: `price - prev_close`) | Absolute change |
| Percent change | Tradier `quote.change_percentage` (or computed) | Relative change |

### Tradier API Call

```python
from eva.tradier import fetch_price, load_config

cfg = load_config("paper")
data = fetch_price(cfg, sym)
# Internally calls: GET /markets/quotes?symbols={sym}
```

`fetch_price` calls `fetch_quote` which hits the Tradier quotes endpoint. It returns a dict with `ticker`, `price`, `previous_close`, `change`, `change_pct`, `timestamp`, `timestamp_iso`.

---

## Formatted Output

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
| Invalid ticker symbol | Tradier API returns error → stderr message, exit code 1 |
| Market closed (weekend/holiday) | Returns last available price (Friday's close). Still works — shows stale timestamp. |
| Network failure | Tradier API request fails → stderr message, exit code 1 |
| Tradier rate limit | Request fails after 3 retries → stderr message, exit code 1 |

---

## No Market Hours Check

This command does NOT check market hours. It always returns data. During market hours, the price is live. Outside market hours, it shows the most recent closing price. This is intentional — users asking "what's IWM at?" should always get an answer.
