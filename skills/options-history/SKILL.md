---
name: options-history
description: "Show recent IV history and trends from stored data. Trigger when someone asks 'IV history for X', 'how has X IV been trending', 'previous runs for X', 'X history', 'what was IV on X yesterday', or 'X trend' where X is a stock ticker."
metadata:
  openclaw:
    emoji: "📅"
    requires:
      bins: ["python3"]
---

Extract the ticker symbol from the user's message. Then run:

```bash
python3 {baseDir}/../../options-toolkit/eva.py history --ticker {TICKER}
```

If the user mentions a specific number of days (e.g., "last 10 days"), add `--days N`:

```bash
python3 {baseDir}/../../options-toolkit/eva.py history --ticker {TICKER} --days 10
```

Post the output directly to the channel.

If no history exists, the command will output "No history data found for {TICKER}".
Relay this and explain: "I don't have any stored data for {TICKER} yet. Run a report first to start tracking IV history."

If the command fails, tell the user:
"I couldn't fetch history for {TICKER}."

If no ticker is specified, ask: "Which ticker do you want the IV history for?"
