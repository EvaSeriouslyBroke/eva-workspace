# TOOLS.md - Options Toolkit Reference

## Toolkit Location

```
~/.openclaw/workspace/options-toolkit/toolkit.py
```

## Commands

```bash
# Price check
python3 toolkit.py price --ticker IWM
python3 toolkit.py price --ticker IWM --json

# Options chain (5 strikes near ATM, ~120 DTE)
python3 toolkit.py chain --ticker IWM
python3 toolkit.py chain --ticker IWM --dte 60

# News + sentiment
python3 toolkit.py news --ticker IWM

# IV history from stored data (no API calls)
python3 toolkit.py history --ticker IWM
python3 toolkit.py history --ticker IWM --days 10

# Full report (always use --force for interactive)
python3 toolkit.py report --ticker IWM --force
```

## Data Location

```
options-toolkit/data/
  {TICKER}/{YYYY}-W{WW}/{YYYY-MM-DD}.json   # Daily snapshots
  cron.log                                     # Cron stderr output
```

## Config

```
options-toolkit/tickers.json    # Tickers + Discord channel for scheduled reports
```

## Cron

Reports run automatically every 30 min during market hours (9:30-16:00 ET, Mon-Fri) via `run_all.sh`. The toolkit's own market hours check filters out pre-9:30 and post-16:00 fires.

Crontab entry:
```
TZ=America/New_York
*/30 9-16 * * 1-5 /home/henry/.openclaw/workspace/options-toolkit/run_all.sh >> /home/henry/.openclaw/workspace/options-toolkit/data/cron.log 2>&1
```

## Key Metrics to Know

| Metric | Bullish Signal | Bearish Signal |
|--------|---------------|----------------|
| P/C Vol Ratio | < 0.8 | > 1.2 |
| P/C OI Ratio | < 0.8 | > 1.2 |
| IV Level | <= 15% (cheap) | > 35% (expensive) |
| IV Trend | Contracting (< -2) | Expanding (> +2) |
| Skew | < -2 (call skew) | > 2 (put skew), > 5 (extreme) |
