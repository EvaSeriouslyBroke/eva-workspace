# Workspace Lookup Skill

**Skill name**: `workspace-lookup`
**Location**: `~/.openclaw/workspace/skills/workspace-lookup/SKILL.md`

Eva's self-reference skill. Lets her navigate her own workspace to understand how things work — docs first, code second.

---

## Trigger Phrases

- "how does X work"
- "where is X defined"
- "what does this command do"
- "why does X happen"
- Investigating unexpected behavior or output
- Any question about her own internals

---

## SKILL.md Content

```yaml
---
name: workspace-lookup
description: >
  Look up how your own system works. Triggered when you need to understand
  "how does X work", "where is X defined", "what does this command do",
  "why does X happen", investigate unexpected behavior, or find out where
  something lives in the codebase. Use this before asking the team about
  your own internals.
metadata:
  openclaw:
    emoji: "\U0001f50d"
---
```

## Execution Flow

### 1. Start With Docs

Read the relevant doc file based on the question. The skill includes a lookup table mapping question types to doc paths (architecture, toolkit commands, paper trading, experiences, skills, scheduling, Discord, etc.).

### 2. If Docs Don't Answer — Read Code

The skill provides a map of the Python codebase (`eva/` package) with each module's responsibility, so Eva knows where to look for implementation details.

### 3. Workspace Config & Identity

Quick reference table for config files, identity files, ticker lists, and memory files.

### 4. Report

Summarize findings. Flag any doc/code disagreements.

---

## Guardrails

- Read-only. Does not modify any files.
- Docs are authoritative over code.
- If the answer isn't in docs or code, Eva says so instead of guessing.
