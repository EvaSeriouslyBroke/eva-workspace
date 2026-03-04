# Cron Setup

How scheduled execution works — the system crontab, timezone handling, scheduled time filtering, and operational details.

---

## Crontab Entries

```cron
35 13,14 * * 1-5 /home/henry/.openclaw/workspace/options-toolkit/run_all.sh >> /home/henry/.openclaw/workspace/options-toolkit/data/cron.log 2>&1
0 15,16,18,19,20 * * 1-5 /home/henry/.openclaw/workspace/options-toolkit/run_all.sh >> /home/henry/.openclaw/workspace/options-toolkit/data/cron.log 2>&1
30 16,17 * * 1-5 /home/henry/.openclaw/workspace/options-toolkit/run_all.sh >> /home/henry/.openclaw/workspace/options-toolkit/data/cron.log 2>&1
59 19,20 * * 1-5 /home/henry/.openclaw/workspace/options-toolkit/run_all.sh >> /home/henry/.openclaw/workspace/options-toolkit/data/cron.log 2>&1
```

### Target Schedule (Eastern Time)

Reports are sent at 6 specific times during each trading day:

| ET Time | Purpose |
|---------|---------|
| 9:35 AM | Market open |
| 11:00 AM | Mid-morning |
| 12:30 PM | Midday |
| 2:00 PM | Mid-afternoon |
| 3:00 PM | Late afternoon |
| 3:59 PM | Market close |

### Cron Entry Breakdown

Each cron line covers both EST and EDT UTC equivalents for a target time, grouped by minute:

| Cron Entry | Covers (EST / EDT) | Target ET Time |
|------------|---------------------|----------------|
| `35 13,14` | 14:35 / 13:35 UTC | 9:35 AM |
| `0 15,16,18,19,20` | 16:00,19:00,20:00 / 15:00,18:00,19:00 UTC | 11:00 AM, 2:00 PM, 3:00 PM |
| `30 16,17` | 17:30 / 16:30 UTC | 12:30 PM |
| `59 19,20` | 20:59 / 19:59 UTC | 3:59 PM |

**11 cron fires per day** (Mon-Fri). ~5 are no-ops (wrong season), filtered by the Python guard.

---

## Timezone Handling

The system runs Debian's Vixie cron (`cron` 3.0pl1), which **does not support** the `TZ=` variable in user crontabs. The cron schedule must be in **UTC**.

### DST-Proof Strategy

Each target ET time maps to two possible UTC times (one for EST, one for EDT). Both are included in the cron entries. The Python `is_scheduled_time()` guard in `toolkit.py` uses `ZoneInfo("America/New_York")` which handles DST automatically — it only allows the fire that matches the current ET time, silently skipping the wrong-season fire. This requires **zero manual maintenance** across DST transitions.

---

## Schedule Guard (in toolkit.py)

The cron fires at both EST and EDT UTC equivalents, but `toolkit.py report` (without `--force`) self-filters to only run at the 6 target ET times:

```python
SCHEDULE = [(9, 35), (11, 0), (12, 30), (14, 0), (15, 0), (15, 59)]

def is_scheduled_time():
    now = datetime.now(ZoneInfo("America/New_York"))

    # Weekday check (0=Monday, 6=Sunday)
    if now.weekday() >= 5:
        return False

    return (now.hour, now.minute) in SCHEDULE
```

### Why Double-Check?

Cron handles the broad UTC coverage. The Python guard handles precision:
- Cron fires at 13:35 UTC during EST — Python says "8:35 AM, not scheduled" (skip)
- Cron fires at 13:35 UTC during EDT — Python says "9:35 AM, scheduled" (run)
- This gives exactly **6 valid executions per trading day**

### Silent Exit Behavior

When the current ET time doesn't match the schedule and `--force` is not passed:
- toolkit.py exits with code 0
- No stdout output
- run_all.sh sees empty output → skips Discord delivery
- Nothing logged (clean skip)

---

## Weekend Handling

Cron only fires Monday through Friday (`1-5`). No weekend executions at all.

---

## NYSE Holidays

The schedule guard does not check for NYSE holidays. On holidays (e.g., MLK Day, Good Friday, Thanksgiving):
- Cron fires normally (it's a weekday)
- toolkit.py runs (schedule check passes based on time, not holiday calendar)
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

## Adding/Removing the Crontab Entries

### View Current Crontab

```bash
crontab -l
```

### Remove All Entries

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
