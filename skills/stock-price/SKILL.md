---
name: stock-price
description: "Check current stock prices and daily changes. Trigger when someone asks 'what's X at', 'price of X', 'how's X doing', 'check X price', or 'X quote' where X is any stock ticker symbol."
metadata:
  openclaw:
    emoji: "💲"
    requires:
      bins: ["python3"]
---

Extract the ticker symbol from the user's message. Then run:

```bash
python3 {baseDir}/../../options-toolkit/eva.py price --ticker {TICKER}
```

Post the output directly to the channel — no additional formatting needed.

If the command fails (exit code 1), tell the user:
"I couldn't fetch the price for {TICKER}. The ticker might be invalid or there might be a network issue."

If no ticker is specified, ask: "Which ticker do you want me to check?"
