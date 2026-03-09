# run_all.sh Script

The cron wrapper script that loops through tickers, runs reports, splits output, and delivers to Discord.

---

## Location

```
~/.openclaw/workspace/options-toolkit/run_all.sh
```

Must be executable: `chmod +x run_all.sh`

---

## What It Does

1. Reads `tickers.json` for the ticker list and Discord channel ID
2. For each ticker:
   a. Runs `eva.py report` — captures output, sends if non-empty
   b. Runs `eva.py summary` — captures output, sends if non-empty
3. Both commands have their own schedule guards, so only the appropriate one produces output at any given time
4. Splits output at `---SPLIT---` markers using a shared `send_chunks` function
5. Sends each chunk to Discord via `openclaw message send`
6. Sleeps between chunks and between tickers

---

## Script (Line by Line)

```bash
#!/usr/bin/env bash
set -euo pipefail
```

- `set -e`: Exit on error
- `set -u`: Error on undefined variables
- `set -o pipefail`: Pipeline fails if any command fails

```bash
export PATH="/home/henry/.npm-global/bin:/usr/local/bin:/usr/bin:$PATH"
```

Ensures `openclaw` and `python3` are on PATH when running from cron's minimal environment. Without this, `openclaw message send` fails with `openclaw: not found`.

```bash
DIR="$(cd "$(dirname "$0")" && pwd)"
```

Get the absolute path to the script's own directory (options-toolkit/).

```bash
TICKERS=$(python3 -c "import json; d=json.load(open('$DIR/tickers.json')); print(' '.join(d['tickers']))")
CHANNEL=$(python3 -c "import json; d=json.load(open('$DIR/tickers.json')); print(d['discord_channel'])")
```

Parse tickers.json using Python one-liners:
- `TICKERS` becomes a space-separated list: `"IWM SPY QQQ"`
- `CHANNEL` becomes the Discord channel ID: `"1474439221140787392"`

```bash
send_chunks() {
  local output="$1"
  local channel="$2"
  echo "$output" | awk -v ch="$channel" '...'
}
```

A shared function that splits text at `---SPLIT---` markers and sends each chunk to Discord via `openclaw message send`. Used for both reports and summaries.

### How the awk Splitting Works

1. **Buffer accumulation**: Each line of output is appended to `buf`
2. **On `---SPLIT---`**: Send the accumulated buffer as a Discord message, then clear it
3. **On EOF**: Send the remaining buffer (the last chunk)
4. **Sleep 1**: Wait 1 second between chunks for Discord rate limiting
5. `\047` is the octal escape for single quote in awk

### Discord Delivery Command

```bash
openclaw message send --channel discord --target 1474439221140787392 --message "chunk text here"
```

| Flag | Value | Description |
|------|-------|-------------|
| `--channel` | `discord` | Delivery platform |
| `--target` | Channel ID | Discord channel to post to |
| `--message` | Chunk text | The message content |

```bash
for TICKER in $TICKERS; do
  # Regular report
  OUTPUT=$(python3 "$DIR/eva.py" report --ticker "$TICKER" 2>/dev/null) || true
  if [ -n "$OUTPUT" ]; then
    send_chunks "$OUTPUT" "$CHANNEL"
    sleep 2
  fi

  # End-of-day summary
  SUMMARY=$(python3 "$DIR/eva.py" summary --ticker "$TICKER" 2>/dev/null) || true
  if [ -n "$SUMMARY" ]; then
    send_chunks "$SUMMARY" "$CHANNEL"
    sleep 2
  fi
done
```

For each ticker, the script runs both `report` and `summary`. Each command has its own schedule guard in Python, so only the appropriate one produces output at any given time:
- Report runs at 6 scheduled times during market hours
- Summary runs only at 4:01 PM ET

**`|| true`** prevents `set -e` from killing the script if eva.py exits with code 1 (e.g., network failure). The script continues to the next ticker.

**`2>/dev/null`** discards stderr from eva.py to keep the cron log clean. Errors are expected occasionally (network hiccups, rate limits).

**`sleep 2`** between tickers prevents flooding Discord and gives the API breathing room.

---

## tickers.json Format

```json
{
  "tickers": ["IWM"],
  "discord_channel": "1474439221140787392"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `tickers` | array of strings | Ticker symbols to run reports for |
| `discord_channel` | string | Discord channel ID for delivery |

### Adding/Removing Tickers

Edit `tickers.json` directly. No restart needed — the script reads it fresh each execution.

```json
{
  "tickers": ["IWM", "SPY", "QQQ"],
  "discord_channel": "1474439221140787392"
}
```

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| eva.py exits with error (code 1) | `set -e` could stop the script. Consider wrapping in `\|\| true` to continue to next ticker. |
| Network failure during report | eva.py fails → empty or error output → skip |
| `openclaw message send` fails | Error goes to cron.log. Chunk is lost. |
| tickers.json missing | Python one-liner fails → script exits |
| Discord rate limit | Unlikely with 1s sleeps, but would appear as send errors in log |

---

## Execution Context

| Property | Value |
|----------|-------|
| Called by | System crontab |
| Working directory | Inherited from cron (typically `/home/henry`) |
| PATH | Inherited from cron (may need `python3` and `openclaw` on PATH) |
| Environment | Minimal cron environment (no user shell profile) |

### PATH Considerations

Cron runs with a minimal PATH. If `python3` or `openclaw` aren't in the default PATH, the crontab entry may need:

```cron
PATH=/usr/local/bin:/usr/bin:/home/henry/.npm-global/bin
```

Or use full paths in the script:

```bash
/usr/bin/python3 "$DIR/eva.py" ...
/home/henry/.npm-global/bin/openclaw message send ...
```

---

## Timing Summary

For a single ticker:
- Report generation: ~3-5 seconds (Tradier API calls)
- 3 chunks × 1s sleep: ~3 seconds
- Total: ~6-8 seconds per ticker

For 3 tickers:
- 3 × 8s + 2 × 2s sleep: ~28 seconds per cron run

Well within the 10-minute interval.
