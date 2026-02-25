---
name: options-chain
description: "Show options chain data with implied volatility for any ticker. Trigger when someone asks for 'options chain', 'calls and puts', 'options for X', 'X chain', 'X strikes', or 'what are X options looking like' where X is a stock ticker."
metadata:
  openclaw:
    emoji: "⛓️"
    requires:
      bins: ["python3"]
---

Extract the ticker symbol from the user's message. Then run:

```bash
python3 {baseDir}/../../options-toolkit/toolkit.py chain --ticker {TICKER}
```

Post the output directly to the channel.

If the command fails (exit code 1), tell the user:
"I couldn't fetch the options chain for {TICKER}. The ticker might not have options available, or there might be a network issue."

If no ticker is specified, ask: "Which ticker do you want the options chain for?"
