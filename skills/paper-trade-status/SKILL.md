---
name: paper-trade-status
description: "Show paper trading portfolio status. Trigger when someone asks 'paper trading status', 'how are your trades doing', 'portfolio status', 'show me your positions', 'paper portfolio'."
metadata:
  openclaw:
    emoji: "\U0001f4bc"
    requires:
      bins: ["python3"]
---

Run the status command:

```bash
python3 {baseDir}/../../options-toolkit/eva.py status
```

Post the full output to Discord as-is. The output is pre-formatted with emoji and dividers for Discord.

If the command fails (exit code 1), tell the user:
"I couldn't fetch my paper trading status. There might be a network issue with the Tradier sandbox."
