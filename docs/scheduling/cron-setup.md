# Cron Setup

How scheduled execution works — the system crontab, timezone handling, market hours filtering, and operational details.

---

## Crontab Entry

```cron
*/30 13-21 * * 1-5 /home/henry/.openclaw/workspace/options-toolkit/run_all.sh >> /home/henry/.openclaw/workspace/options-toolkit/data/cron.log 2>&1
```

### Field-by-Field Breakdown

| Field | Value | Meaning |
|-------|-------|---------|
| Minute | `*/30` | Every 30 minutes (0, 30) |
| Hour | `13-21` | UTC hours covering market hours in both EST and EDT (see Timezone Handling) |
| Day of month | `*` | Any day |
| Month | `*` | Any month |
| Day of week | `1-5` | Monday (1) through Friday (5) |
| Command | `run_all.sh` | Full path to wrapper script |
| Output | `>> cron.log 2>&1` | Append stdout+stderr to log |

### Firing Schedule

On a typical Monday-Friday:
```
9:00  9:30
10:00 10:30
11:00 11:30
12:00 12:30
13:00 13:30
14:00 14:30
15:00 15:30
16:00 16:30
```

**16 fires per day**, but only the ones during market hours (9:30-16:00) will produce output.

---

## Timezone Handling

The system runs Debian's Vixie cron (`cron` 3.0pl1), which **does not support** the `TZ=` variable in user crontabs. The cron schedule must be in **UTC**.

### DST-Proof Strategy

Rather than adjusting the cron twice a year, the cron window is set wide enough to cover market hours under both EST and EDT:

- **EST** (UTC-5): Market 9:30–16:00 ET = 14:30–21:00 UTC
- **EDT** (UTC-4): Market 9:30–16:00 ET = 13:30–20:00 UTC
- **Cron window**: `13-21` UTC — covers both seasons

The Python `is_market_hours()` guard in `toolkit.py` uses `ZoneInfo("America/New_York")` which handles DST automatically. Fires outside market hours produce no output and are silently skipped. This means a few extra no-op cron fires per day (~2-3 depending on season), but it requires **zero manual maintenance** across DST transitions.

---

## Market Hours Guard (in toolkit.py)

The cron fires broadly (9:00-16:50), but `toolkit.py report` (without `--force`) self-filters:

```python
from datetime import datetime
from zoneinfo import ZoneInfo

def is_market_hours():
    now = datetime.now(ZoneInfo("America/New_York"))

    # Weekday check (0=Monday, 6=Sunday)
    if now.weekday() >= 5:
        return False

    # Time check
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)

    return market_open <= now <= market_close
```

### Why Double-Check?

Cron handles the broad window (Mon-Fri, 9-16). The Python guard handles precision:
- Cron fires at 9:00 — Python says "not yet" (before 9:30)
- Cron fires at 16:30 — Python says "market closed" (after 16:00)
- This gives exactly 14 valid executions per trading day:
  ```
  9:30, 10:00, 10:30, 11:00, 11:30, 12:00, 12:30, 13:00, 13:30, 14:00, 14:30, 15:00, 15:30, 16:00
  ```

### Silent Exit Behavior

When outside market hours and `--force` is not passed:
- toolkit.py exits with code 0
- No stdout output
- run_all.sh sees empty output → skips Discord delivery
- Nothing logged (clean skip)

---

## Weekend Handling

Cron only fires Monday through Friday (`1-5`). No weekend executions at all.

---

## NYSE Holidays

The market hours guard does not check for NYSE holidays. On holidays (e.g., MLK Day, Good Friday, Thanksgiving):
- Cron fires normally (it's a weekday)
- toolkit.py runs (market hours check passes based on time, not holiday calendar)
- yfinance returns stale data (previous close) or possibly empty chains
- Report may show yesterday's data — not harmful, but not useful

~9 holidays/year are affected. See [design-decisions.md](../architecture/design-decisions.md#why-not-handle-nyse-holidays) for rationale.

---

## Log File

### Location

```
~/.openclaw/workspace/options-toolkit/data/cron.log
```

### What Gets Logged

- stderr from toolkit.py (error messages, warnings)
- Any stdout from run_all.sh itself (e.g., if it prints diagnostic messages)
- Successful Discord sends produce no log output (the message goes to Discord, not the log)

### What Doesn't Get Logged

- The actual report content (it goes to Discord via `openclaw message send`)
- Silent skips (no output = nothing to log)

### Log Rotation

No automatic log rotation. The log grows indefinitely. Truncate manually if needed: `> cron.log`

---

## Adding/Removing the Crontab Entry

### View Current Crontab

```bash
crontab -l
```

### Add Entry

```bash
(crontab -l 2>/dev/null; echo 'TZ=America/New_York'; echo '*/10 9-16 * * 1-5 /home/henry/.openclaw/workspace/options-toolkit/run_all.sh >> /home/henry/.openclaw/workspace/options-toolkit/data/cron.log 2>&1') | crontab -
```

### Remove Entry

```bash
crontab -l | grep -v 'run_all.sh' | crontab -
```

### Verify It's Running

```bash
# Check cron service
systemctl status cron

# Check recent log entries
tail -20 ~/.openclaw/workspace/options-toolkit/data/cron.log

# Watch live
tail -f ~/.openclaw/workspace/options-toolkit/data/cron.log
```

---

## Why Not OpenClaw Cron?

See [design-decisions.md](../architecture/design-decisions.md#why-system-crontab-over-openclaw-cron). In short: system cron is free, fast, and deterministic. OpenClaw cron burns tokens on LLM calls for a mechanical task.
