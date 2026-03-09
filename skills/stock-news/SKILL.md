---
name: stock-news
description: "Quick headline summary for a stock ticker — no deep analysis. ONLY use this when you need a fast, formatted news snippet (e.g. composing a multi-part response). For any direct user request about news — including 'X news', 'news on X', 'what's going on with X' — use the stock-news-deep skill instead, which provides real analysis."
metadata:
  openclaw:
    emoji: "📰"
    requires:
      bins: ["python3"]
---

Extract the ticker symbol from the user's message. Then run:

```bash
python3 {baseDir}/../../options-toolkit/eva.py news --ticker {TICKER}
```

Post the output directly to the channel.

If the command fails (exit code 1), tell the user:
"I couldn't fetch news for {TICKER}. There might be a network issue."

If no ticker is specified, ask: "Which ticker do you want news for?"
