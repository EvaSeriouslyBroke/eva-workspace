---
name: options-report
description: "Run a full options analysis report with IV data, sentiment, and trading recommendations. Trigger when someone asks to 'run the report', 'full analysis', 'options report', 'what's the play on X', 'how's X looking', 'analyze X options', or 'send me an analysis' for any stock ticker X."
metadata:
  openclaw:
    emoji: "🎯"
    requires:
      bins: ["python3"]
---

Extract the ticker symbol from the user's message. Then run with `--force` (always, since this is interactive):

```bash
python3 {baseDir}/../../options-toolkit/toolkit.py report --ticker {TICKER} --force
```

The output will be long (~8000-10000 chars) and contain `---SPLIT---` markers.

1. Capture the entire stdout from the command
2. Split the text at each `---SPLIT---` line
3. For each chunk:
   a. Trim leading/trailing whitespace
   b. Send as a separate Discord message to the channel
   c. Wait ~1 second before sending the next chunk
4. Do NOT add any additional commentary between chunks

If the command fails (exit code 1), tell the user:
"I couldn't generate the report for {TICKER}. The ticker might be invalid or there might be a network issue. Check if yfinance is working."

If the output is empty or has no `---SPLIT---` markers, something unexpected happened. Report the raw output or error.

If no ticker is specified, ask: "Which ticker do you want the full analysis for?"
