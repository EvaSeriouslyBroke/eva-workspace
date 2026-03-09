# Paper Trade Status Skill

**Skill name**: `paper-trade-status`
**Location**: `~/.openclaw/workspace/skills/paper-trade-status/SKILL.md`

Interactive skill that shows Eva's paper trading portfolio status.

---

## Trigger Phrases

- "paper trading status"
- "how are your trades doing"
- "portfolio status"
- "show me your positions"
- "paper portfolio"

---

## SKILL.md Content

```yaml
---
name: paper-trade-status
description: >
  Show paper trading portfolio status. Trigger when someone asks "paper trading
  status", "how are your trades doing", "portfolio status", "show me your
  positions", "paper portfolio".
metadata:
  openclaw:
    emoji: "💼"
    requires:
      bins: ["python3"]
---
```

## Exec Command

```bash
python3 {baseDir}/../../options-toolkit/eva.py status
```

## Output Handling

Post the full output to Discord as-is. The output is pre-formatted with emoji and dividers for Discord.

## Error Handling

If the command fails (exit code 1), tell the user:
"I couldn't fetch my paper trading status. There might be a network issue with the Tradier sandbox."
