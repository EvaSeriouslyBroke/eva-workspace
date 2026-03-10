# Paper Trade Strategy Skill

**Skill name**: `paper-trade-strategy`
**Location**: `~/.openclaw/workspace/skills/paper-trade-strategy/SKILL.md`

Modifies the paper trading strategy (PAPER.md) when users suggest experiments or strategy changes. Enforces no-assumptions writing rules so the strategy stays discovery-oriented.

---

## Trigger Phrases

- "test this strategy"
- "try this DTE"
- "add this to paper strategy"
- "experiment with X"
- "change paper trading rules"
- Any request to alter how Eva trades in paper mode

---

## SKILL.md Content

```yaml
---
name: paper-trade-strategy
description: >
  Modify the paper trading strategy (PAPER.md). Triggered when a user suggests
  a strategy to test, asks to add an experiment, says "try this DTE", "test
  this approach", "add this to paper strategy", "change paper trading rules",
  "experiment with X", or any request to alter how Eva trades in paper mode.
metadata:
  openclaw:
    emoji: "\U0001f9ea"
---
```

## Execution Flow

### 1. Load Context

Read current PAPER.md and experience README.md.

### 2. Understand the Request

Categorize: new experiment, rule change, or removal.

### 3. Write the Change

For new experiments, follow a strict format:
- Goal phrased as a question, not an answer
- "What to Test" lists actions, not predictions
- Required tagging (must include regime + DTE bucket tags)
- Volume-based success criteria

### 4. Verify Against No-Assumptions Rules

Re-read the entry and check every sentence:
1. No predictions ("best for", "works well with", "preferred for")
2. No conviction ("tends to", "usually", "expect")
3. Questions, not answers ("Does X work?" not "X works because Y")
4. Actions, not beliefs ("Try X" not "X is good for Y")
5. Data-driven success criteria ("after N trades, compare") not confirmation ("confirm X works")

### 5. Report

Post the change to Discord.

---

## Guardrails

- Modifies ONLY `strategy/PAPER.md`
- Never modifies experience files, skills, or toolkit code
- Never adds assumptions, predictions, or convictions to the strategy
