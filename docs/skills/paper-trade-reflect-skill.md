# Paper Trade Reflect Skill

**Skill name**: `paper-trade-reflect`
**Location**: `~/.openclaw/workspace/skills/paper-trade-reflect/SKILL.md`

Processes closed paper trades and creates/updates experience files. Runs in a dedicated session so Eva can focus entirely on reflection without the cognitive load of trading decisions.

---

## Trigger Phrases

- "reflect on trades"
- "process closed positions"
- "update experiences"
- Also triggered automatically by OpenClaw cron ~7 minutes after each evaluate cycle

---

## SKILL.md Content

```yaml
---
name: paper-trade-reflect
description: >
  Process recently closed paper trades and update experience files.
  Triggered by cron after evaluation cycles, or when asked to
  "reflect on trades", "process closed positions", "update experiences".
metadata:
  openclaw:
    emoji: "\U0001f4dd"
    requires:
      bins: ["python3"]
---
```

## Execution Flow

### 1. Load Context

Read experience system docs and strategy rules.

### 2. Fetch Pending Updates

```bash
python3 {baseDir}/../../options-toolkit/eva.py pending-experience
```

If the array is empty, skip to maintenance.

### 3. Process Each Closed Position

For each pending entry:
1. Analyze the trade outcome using position snapshots, entry/close reasons, and market context
2. Find or create the relevant experience file
3. Add evidence with `[paper]` tag and `[supporting]`/`[contradicting]` label
4. Update Analysis and confidence if warranted
5. Update INDEX.md if a new file was created

### 4. Clear Pending Updates

```bash
python3 {baseDir}/../../options-toolkit/eva.py pending-experience --clear
```

Only after all experience files are successfully written.

### 5. Experience Maintenance

Roll old evidence entries into Summary if Recent has more than 5. Look for cross-ticker patterns.

### 6. Report

Post a brief note about what was learned. Stay silent if nothing to process.

---

## Guardrails

- Does NOT make trading decisions
- Does NOT run `evaluate`, `buy`, or `sell`
- Focus only on experience creation, updates, and maintenance

---

## Scheduling

Runs via OpenClaw cron at `:07, :22, :37, :52` during market hours (7 minutes after each evaluate cycle at `:00, :15, :30, :45`). The evaluate job takes ~96 seconds, so 7 minutes provides ample buffer.

The pending file is durable — if the reflect skill fails or finds nothing, the data survives for the next cycle.
