# Discord Message Delivery

How reports get from stdout to Discord messages — chunk splitting, rate limiting, and error handling for both scheduled and interactive delivery.

---

## Discord's 2000-Character Limit

Discord messages are capped at 2000 characters. Our full report is ~2500-4000 characters. It must be split into multiple messages.

---

## Split Strategy

### `---SPLIT---` Markers

The report output contains literal `---SPLIT---` lines at logical section boundaries. These are the split points — each section between markers becomes one Discord message.

### 3 Chunks

| Chunk | Content | Target Size |
|-------|---------|-------------|
| 1 | History check, header, price | ~600-900 chars |
| 2 | Target expiry, call table, put table | ~1200-1800 chars |
| 3 | IV summary (averages, volume, OI, skew) + footer + save confirmation | ~700-1100 chars |

### Safety Margin

Each chunk targets **< 1900 characters** (100-char safety margin below the 2000 limit). This accounts for:
- Variable-length ticker names
- Long headlines
- Multiple conditional lines firing at once

If a chunk somehow exceeds 2000 chars, the `openclaw message send` command will fail for that chunk. This should be rare given the formatting constraints.

---

## Scheduled Delivery (run_all.sh)

### Flow

```
eva.py report → stdout with ---SPLIT--- → awk splits → openclaw message send per chunk
```

### Splitting Logic (awk)

```awk
BEGIN { buf="" }
/^---SPLIT---$/ {
  if (buf != "") {
    system("openclaw message send --channel discord --target " ch " --message '" buf "'")
    system("sleep 1")
  }
  buf=""
  next
}
{ buf = buf (buf=="" ? "" : "\n") $0 }
END {
  if (buf != "") {
    system("openclaw message send --channel discord --target " ch " --message '" buf "'")
  }
}
```

**How it works:**
1. Read lines into a buffer
2. When `---SPLIT---` is encountered, send the buffer as a message, clear it
3. At end of input, send whatever remains in the buffer
4. Sleep 1 second between messages

### Rate Limiting

| Between | Delay | Why |
|---------|-------|-----|
| Chunks (same ticker) | 1 second | Avoid Discord rate limits |
| Tickers | 2 seconds | Extra breathing room, orderly delivery |

### Discord Delivery Command

```bash
openclaw message send \
  --channel discord \
  --target 1474439221140787392 \
  --message "$chunk_text"
```

| Parameter | Value | Description |
|-----------|-------|-------------|
| `--channel` | `discord` | Platform identifier |
| `--target` | Channel ID string | Which Discord channel to post to |
| `--message` | Chunk text | Message content (the chunk) |

### Target Channel

Configured in `tickers.json`:
```json
{
  "discord_channel": "1474439221140787392"
}
```

This is the channel where scheduled reports are posted. All tickers go to the same channel.

---

## Interactive Delivery (Eva)

### Flow

```
User asks → Eva triggers skill → exec eva.py → Eva captures stdout → Eva splits → Eva sends
```

### How Eva Handles It

The options-report skill instructs Eva to:
1. Run `eva.py report --ticker {TICKER} --force`
2. Capture the full stdout
3. Split the text at `---SPLIT---` lines
4. Send each chunk as a separate Discord message to the **requesting channel**
5. Wait ~1 second between messages

### Key Differences from Scheduled

| Aspect | Scheduled | Interactive |
|--------|-----------|-------------|
| Target channel | From tickers.json (fixed) | Requesting channel (wherever the user asked) |
| `--force` flag | Not passed | Always passed |
| Who splits | awk in run_all.sh | Eva (agent) |
| Who sends | `openclaw message send` CLI | Eva's built-in Discord posting |
| Error feedback | Goes to cron.log | Eva tells the user |

---

## Error Handling

### `openclaw message send` Failures

| Error | Cause | Handling |
|-------|-------|---------|
| Message too long | Chunk > 2000 chars | Send fails. Error logged. Chunk lost. |
| Rate limited | Too many messages too fast | Discord returns 429. `openclaw` may retry internally. |
| Network error | Connectivity issue | Send fails. Error logged. |
| Invalid channel | Channel ID wrong or bot not in channel | Send fails. Error logged. |
| Bot offline | OpenClaw gateway not running | Send fails. Error logged. |

### Mitigation

- **Chunk sizing**: Report formatting ensures chunks stay well under 2000 chars
- **Sleep between messages**: 1-second delay prevents rate limiting
- **Continue on failure**: If one chunk fails, remaining chunks should still be attempted (the awk script naturally does this since each `system()` call is independent)

### Monitoring

Check for delivery failures:
```bash
# Recent errors in cron log
grep -i "error\|fail" ~/.openclaw/workspace/options-toolkit/data/cron.log | tail -20

# Check OpenClaw gateway status
systemctl --user status openclaw-gateway

# Verify Discord bot is connected
openclaw status
```

---

## Message Ordering

Discord displays messages in the order received. With 1-second delays between chunks, they arrive in order:

```
Message 1: Header + Price                 (t=0s)
Message 2: Options Tables                 (t=1s)
Message 3: IV Summary + Footer            (t=2s)
```

Total delivery time: ~2-3 seconds per ticker.

---

## Platform Formatting Notes

From AGENTS.md: Discord does NOT support markdown tables. The options tables use stacked 3-line cards inside code blocks for a mobile-friendly layout (~42 chars wide max). Emoji headers (📈 CALLS, 📉 PUTS) sit outside the code block so they render properly.

Discord DOES support:
- Emoji (used extensively: 🟢 🟡 🔴 🎯 📰 📈 📉 📊 🔍 ⚠️ ✅ 💰 📜 💼)
- Monospace blocks (``` ``` for code blocks)
- Basic formatting (**bold**, *italic*)

### Mobile-Friendly Design

The options tables use stacked 3-line cards inside code blocks (~42 chars wide) to fit mobile screens. Dividers are 40 characters wide. Emoji headers (📈 CALLS, 📉 PUTS) sit outside code blocks since emoji don't render well inside them.
