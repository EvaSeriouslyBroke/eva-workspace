---
name: options-summary
description: "Run an end-of-day summary with intraday analysis of IV, volume, skew, OI, and price movements. Trigger when someone asks for a 'summary of today', 'end of day summary', 'how did X do today', 'daily recap', 'today's recap', 'day summary for X', 'wrap up on X', or 'what happened with X today' for any stock ticker X."
metadata:
  openclaw:
    emoji: "📊"
    requires:
      bins: ["python3"]
---

Extract the ticker symbol from the user's message. Then run with `--force` (always, since this is interactive):

```bash
python3 {baseDir}/../../options-toolkit/eva.py summary --ticker {TICKER} --force
```

The output will contain `---SPLIT---` markers.

1. Capture the entire stdout from the command
2. Split the text at each `---SPLIT---` line
3. For each chunk:
   a. Trim leading/trailing whitespace
   b. Send as a separate Discord message to the channel
   c. Wait ~1 second before sending the next chunk
4. Do NOT add any additional commentary between chunks

If the command fails (exit code 1), tell the user:
"I couldn't generate the summary for {TICKER}. The ticker might be invalid or there might be a network issue."

If the output is empty, tell the user:
"No summary data available for {TICKER} today. The summary needs at least 2 valid snapshots from today's trading session."

If no ticker is specified, ask: "Which ticker do you want the end-of-day summary for?"
