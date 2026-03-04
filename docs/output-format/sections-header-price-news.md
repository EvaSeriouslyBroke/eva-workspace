# Sections 1-3: History, Header, Price

These three sections form the first chunk of the report (before the first `---SPLIT---` marker).

---

## Section 1: History Check

One line indicating whether previous data was found.

### If previous data exists:

```
✓ Previous data from: 2026-02-20 09:30:00 (40 minutes ago)
```

The timestamp is the `timestamp` field from the previous snapshot. The "time ago" is computed relative to the current run time.

#### Time Ago Formatting

| Gap | Format | Example |
|-----|--------|---------|
| < 60 minutes | `{N} minutes ago` | `40 minutes ago` |
| 1-23 hours | `{N} hours ago` | `3 hours ago` |
| 1-6 days | `{N} days ago` | `2 days ago` |
| > 6 days | `{N} days ago` | `8 days ago` |

Use the largest appropriate unit. `90 minutes ago` → `1 hours ago` (keep it simple, always use the hour unit after 60 min).

### If first run:

```
ℹ️  No previous IV data found - first run
```

---

## Section 2: Main Header

```
==========================================================================================
  🎯 {TICKER} OPTIONS TRADING ANALYZER
==========================================================================================
```

- `{TICKER}` is the uppercase ticker symbol (e.g., `IWM`, `SPY`)
- Two lines of 90 `=` characters above and below
- Two leading spaces before the emoji
- This is NOT hardcoded to "IWM" — it uses whatever ticker was passed

---

## Section 3: Price & Metadata

Three lines:

```
Current IWM Price: $210.45 🟢 (+$0.65 / +0.31%)
Previous Close: $209.80
Analysis Time: 2026-02-20 10:30:00
```

### Line 1: Current Price

```
Current {TICKER} Price: ${price} {emoji} ({sign}${abs_change} / {sign}{change_pct}%)
```

| Component | Rule |
|-----------|------|
| `{TICKER}` | Uppercase ticker symbol |
| `${price}` | 2 decimal places |
| `{emoji}` | 🟢 if change > 0, 🔴 if change < 0, 🟡 if change = 0 |
| `${abs_change}` | Absolute dollar change, 2 decimals, with sign |
| `{change_pct}` | Percentage change, 2 decimals, with sign |

### Line 2: Previous Close

```
Previous Close: ${prev_close}
```

Simple, no emoji, 2 decimal places.

### Line 3: Analysis Time

```
Analysis Time: {YYYY-MM-DD HH:MM:SS}
```

Current time in Eastern timezone (America/New_York), 24-hour format.

---

## Chunk Boundary

After Section 3, insert the first `---SPLIT---` marker:

```
Analysis Time: 2026-02-20 10:30:00
---SPLIT---
Target Expiration: ...
```

This keeps Sections 1-3 in the first Discord message.

---

## News (Disabled)

News fetching and formatting functions (`fetch_news`, `format_news`) exist in toolkit.py but are not included in the report output. The `news` subcommand still works standalone via `toolkit.py news --ticker TICKER`.
