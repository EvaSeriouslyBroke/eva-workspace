# Snapshots Command

The `snapshots` subcommand queries stored market snapshots with two modes: **browse** (date-ranged, field-filtered) and **peaks** (find price/IV extremes with full context).

---

## Usage

```
python3 eva.py snapshots --ticker <SYM> [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--fields FIELDS]
python3 eva.py snapshots --ticker <SYM> --peaks [--days N]
```

### Examples

```bash
python3 eva.py snapshots --ticker AMD --from 2026-03-06 --to 2026-03-09
python3 eva.py snapshots --ticker AMD --fields iv,trends
python3 eva.py snapshots --ticker AMD --peaks --days 30
```

---

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--ticker` | *(required)* | Ticker symbol |
| `--from` | 7 days ago | Start date (YYYY-MM-DD) |
| `--to` | today | End date (YYYY-MM-DD) |
| `--fields` | all | Comma-separated field groups: `iv`, `intraday`, `trends`, `iv_context`, `sentiment`, `broader_market` |
| `--peaks` | off | Switch to peaks mode (find price/IV peaks and troughs) |
| `--days` | 30 | Lookback days for peaks mode |
| `--all-intraday` | off | Show all intraday snapshots instead of last-of-day |

---

## Browse Mode (Default)

Returns snapshots within the date range, filtered to requested field groups. By default shows the last snapshot of each day; `--all-intraday` includes every intraday snapshot.

### Output

```json
{
  "ticker": "AMD",
  "from": "2026-03-06",
  "to": "2026-03-09",
  "count": 3,
  "snapshots": [
    {
      "ts": "2026-03-06T15:59:00-05:00",
      "price": 118.50,
      "avg_call_iv": 42.10,
      "avg_put_iv": 44.30
    }
  ]
}
```

---

## Peaks Mode

Finds price and IV extremes across the lookback window. Each peak/trough includes the full snapshot context.

### Output

```json
{
  "ticker": "AMD",
  "days": 30,
  "price_peak": { "ts": "...", "price": 125.40, "..." : "..." },
  "price_trough": { "ts": "...", "price": 110.20, "..." : "..." },
  "iv_peak": { "ts": "...", "avg_call_iv": 48.50, "..." : "..." },
  "iv_trough": { "ts": "...", "avg_call_iv": 35.20, "..." : "..." },
  "current": { "ts": "...", "price": 118.50, "..." : "..." }
}
```

---

## What It Reads

This command reads from the local data store:

```
~/.openclaw/workspace/options-toolkit/data/{mode}/{TICKER}/snapshots/{YYYY-MM-DD}.json
```

Falls back to the legacy `iv/` directory if no `snapshots/` data exists for a given date.

---

## No Market Hours Check

This command reads local files, not live data. It works anytime.
