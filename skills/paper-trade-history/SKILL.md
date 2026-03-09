---
name: paper-trade-history
description: "Show paper trade history with reasoning. Trigger when someone asks 'paper trade history', 'recent trades', 'trade log', 'what trades have you made', 'show me your trades'."
metadata:
  openclaw:
    emoji: "\U0001f4dc"
    requires:
      bins: ["python3"]
---

Run the history command:

```bash
python3 {baseDir}/../../options-toolkit/eva.py trade-history
```

Post the full output to Discord as-is. The output is pre-formatted with emoji and dividers for Discord.

If the command fails (exit code 1), tell the user:
"I couldn't fetch my trade history. There might be a network issue with the Tradier sandbox."
