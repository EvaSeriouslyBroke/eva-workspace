# Cron Setup

How scheduled execution works — the system crontab, timezone handling, scheduled time filtering, and operational details.

---

## Crontab Entries

```cron
31 13,14 * * 1-5 /home/henry/.openclaw/workspace/options-toolkit/run_all.sh >> /home/henry/.openclaw/workspace/options-toolkit/data/cron.log 2>&1
0 15,16,18,19,20 * * 1-5 /home/henry/.openclaw/workspace/options-toolkit/run_all.sh >> /home/henry/.openclaw/workspace/options-toolkit/data/cron.log 2>&1
30 16,17 * * 1-5 /home/henry/.openclaw/workspace/options-toolkit/run_all.sh >> /home/henry/.openclaw/workspace/options-toolkit/data/cron.log 2>&1
59 19,20 * * 1-5 /home/henry/.openclaw/workspace/options-toolkit/run_all.sh >> /home/henry/.openclaw/workspace/options-toolkit/data/cron.log 2>&1
1 20,21 * * 1-5 /home/henry/.openclaw/workspace/options-toolkit/run_all.sh >> /home/henry/.openclaw/workspace/options-toolkit/data/cron.log 2>&1
```

### Target Schedule (Eastern Time)

Reports are sent at 6 specific times during each trading day, plus an end-of-day summary:

| ET Time | Purpose |
|---------|---------|
| 9:31 AM | Market open |
| 11:00 AM | Mid-morning |
| 12:30 PM | Midday |
| 2:00 PM | Mid-afternoon |
| 3:00 PM | Late afternoon |
| 3:59 PM | Market close |
| 4:01 PM | End-of-day summary |

### Cron Entry Breakdown

Each cron line covers both EST and EDT UTC equivalents for a target time, grouped by minute:

| Cron Entry | Covers (EST / EDT) | Target ET Time |
|------------|---------------------|----------------|
| `31 13,14` | 14:31 / 13:31 UTC | 9:31 AM |
| `0 15,16,18,19,20` | 16:00,19:00,20:00 / 15:00,18:00,19:00 UTC | 11:00 AM, 2:00 PM, 3:00 PM |
| `30 16,17` | 17:30 / 16:30 UTC | 12:30 PM |
| `59 19,20` | 20:59 / 19:59 UTC | 3:59 PM |
| `1 20,21` | 21:01 / 20:01 UTC | 4:01 PM (summary) |

**13 cron fires per day** (Mon-Fri). ~6 are no-ops (wrong season), filtered by the Python guards.

---

## Timezone Handling

The system runs Debian's Vixie cron (`cron` 3.0pl1), which **does not support** the `TZ=` variable in user crontabs. The cron schedule must be in **UTC**.

### DST-Proof Strategy

Each target ET time maps to two possible UTC times (one for EST, one for EDT). Both are included in the cron entries. The Python `is_scheduled_time()` guard in `eva.py` uses `ZoneInfo("America/New_York")` which handles DST automatically — it only allows the fire that matches the current ET time, silently skipping the wrong-season fire. This requires **zero manual maintenance** across DST transitions.

---

## Schedule Guard (in eva.py)

The cron fires at both EST and EDT UTC equivalents, but eva.py self-filters using two schedule guards:

```python
SCHEDULE = [(9, 31), (11, 0), (12, 30), (14, 0), (15, 0), (15, 59)]
SUMMARY_SCHEDULE = [(16, 1)]

def is_scheduled_time():  # Used by report
    now = datetime.now(ZoneInfo("America/New_York"))
    if now.weekday() >= 5:
        return False
    return (now.hour, now.minute) in SCHEDULE

def is_summary_time():  # Used by summary
    now = datetime.now(ZoneInfo("America/New_York"))
    if now.weekday() >= 5:
        return False
    return (now.hour, now.minute) in SUMMARY_SCHEDULE
```

### Why Double-Check?

Cron handles the broad UTC coverage. The Python guards handle precision:
- Cron fires at 13:31 UTC during EST — Python says "8:31 AM, not scheduled" (skip)
- Cron fires at 13:31 UTC during EDT — Python says "9:31 AM, scheduled" (run)
- This gives exactly **6 report runs + 1 summary run per trading day**

### Silent Exit Behavior

When the current ET time doesn't match the schedule and `--force` is not passed:
- eva.py exits with code 0
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
- eva.py runs (schedule check passes based on time, not holiday calendar)
- Tradier returns stale data (previous close) or the market is simply closed
- Report may show yesterday's data — not harmful, but not useful

~9 holidays/year are affected. See [design-decisions.md](../architecture/design-decisions.md#why-not-handle-nyse-holidays) for rationale.

---

## Log File

### Location

```
~/.openclaw/workspace/options-toolkit/data/cron.log
```

### What Gets Logged

- Any stdout from run_all.sh itself (e.g., diagnostic messages)
- Errors from `openclaw message send` calls
- Successful Discord sends produce no log output (the message goes to Discord, not the log)
- Note: eva.py stderr is discarded by the script (`2>/dev/null`) and does not appear in this log

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

## OpenClaw Cron Jobs (Paper Trading)

Paper trading uses OpenClaw cron (not system cron) because the tasks require LLM reasoning.

| Job | Schedule (ET) | Purpose |
|-----|--------------|---------|
| `paper-trade-eval` | `:00, :15, :30, :45` (9-15 Mon-Fri) | Autonomous trading evaluation |
| `paper-trade-reflect` | `:07, :22, :37, :52` (9-15 Mon-Fri) | Experience creation from closed trades |

The reflect job runs ~7 minutes after each evaluate job, giving evaluate time to complete (~96s typical). Both deliver to the `paper-trading` Discord channel.

Config: `~/.openclaw/cron/jobs.json`

---

## Why Not OpenClaw Cron for Reports?

See [design-decisions.md](../architecture/design-decisions.md#why-system-crontab-over-openclaw-cron). In short: system cron is free, fast, and deterministic. OpenClaw cron burns tokens on LLM calls for a mechanical task. Paper trading uses OpenClaw cron because evaluation and reflection require LLM reasoning.
