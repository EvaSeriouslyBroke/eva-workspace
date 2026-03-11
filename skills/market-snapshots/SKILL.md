---
name: market-snapshots
description: "Browse historical market snapshots or find price/IV peaks and troughs. Trigger when someone asks 'snapshots for X', 'X snapshot history', 'show me X peaks', 'when was X IV highest', 'X price peak last month', 'market data for X last week', or 'X snapshot between dates' where X is a stock ticker."
metadata:
  openclaw:
    emoji: "📸"
    requires:
      bins: ["python3"]
---

Extract the ticker symbol from the user's message.

## Browse Mode

If the user wants to see snapshots for a date range:

```bash
python3 {baseDir}/../../options-toolkit/eva.py snapshots --ticker {TICKER}
```

Optional flags based on user request:
- Date range: `--from YYYY-MM-DD --to YYYY-MM-DD` (default: last 7 days)
- Specific data: `--fields iv,trends,sentiment` (available: iv, intraday, trends, iv_context, sentiment, broader_market)
- All intraday data points: `--all-intraday` (default: last snapshot per day)

## Peaks Mode

If the user asks about peaks, troughs, highs, lows, or extremes:

```bash
python3 {baseDir}/../../options-toolkit/eva.py snapshots --ticker {TICKER} --peaks
```

Optional: `--days N` to change lookback period (default: 30).

Returns price peak/trough and IV peak/trough with full snapshot context at each moment — trends, sentiment, broader market, everything captured at that point.

## Output

Output is JSON. Summarize the key findings for the user. For peaks mode, highlight the dates and conditions at each extreme.

## Error Handling

If no snapshots exist: "I don't have any stored snapshots for {TICKER} yet. Snapshots are recorded during each evaluation cycle."

If no ticker is specified: "Which ticker do you want snapshots for?"
