# Paper Trade History Skill

**Skill name**: `paper-trade-history`
**Location**: `~/.openclaw/workspace/skills/paper-trade-history/SKILL.md`

Interactive skill that shows Eva's paper trade history with reasoning.

---

## Trigger Phrases

- "paper trade history"
- "recent trades"
- "trade log"
- "what trades have you made"
- "show me your trades"

---

## SKILL.md Content

```yaml
---
name: paper-trade-history
description: >
  Show paper trade history with reasoning. Trigger when someone asks "paper
  trade history", "recent trades", "trade log", "what trades have you made",
  "show me your trades".
metadata:
  openclaw:
    emoji: "📜"
    requires:
      bins: ["python3"]
---
```

## Exec Command

```bash
python3 {baseDir}/../../options-toolkit/eva.py trade-history
```

## Output Handling

Post the full output to Discord as-is. The output is pre-formatted with emoji and dividers for Discord.

## Error Handling

If the command fails (exit code 1), tell the user:
"I couldn't fetch my trade history. There might be a network issue with the Tradier sandbox."
