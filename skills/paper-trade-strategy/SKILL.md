---
name: paper-trade-strategy
description: "Modify the paper trading strategy (PAPER.md). Triggered when a user suggests a strategy to test, asks to add an experiment, says 'try this DTE', 'test this approach', 'add this to paper strategy', 'change paper trading rules', 'experiment with X', or any request to alter how Eva trades in paper mode."
metadata:
  openclaw:
    emoji: "\U0001f9ea"
---

Modify the paper trading strategy. Follow every step in order.

## 1. Load Context

1. Read `{baseDir}/../../strategy/PAPER.md` — current strategy
2. Read `{baseDir}/../../experience/README.md` — experience tagging rules

Understand the current Testing section entries before making changes.

## 2. Understand the Request

Identify what the user wants to change or test. Categorize:
- **New experiment** — a strategy, DTE range, or condition to test
- **Rule change** — modifying Hard Constraints, Entry, Exit, or Learning Priority
- **Removal** — removing a Testing entry or rule

## 3. Write the Change

### For New Experiments (Testing section entries)

Follow this format exactly:

```markdown
### {Experiment Title} ({YYYY-MM-DD})
**Source:** {User name or Eva} | **Status:** Active

**Goal:** {What we want to discover — phrased as a question, not an answer}

**What to Test:**
- {Specific conditions, setups, or variations to try}
- {Each item is an action, not a prediction}

**Tagging:**
- {Required tags for experiences created from this experiment}
- Always include: market regime tag, DTE bucket tag

**Success Criteria:** {How we know we've learned enough to draw conclusions}
```

### No-Assumptions Rules

These rules are absolute. Every Testing entry MUST follow them:

1. **No predictions.** Never write "best for", "works well with", "preferred for",
   or any language that assumes an outcome before testing. The point is to find out.
2. **No conviction.** Never write "X tends to", "X usually", "expect Y". We don't
   know yet — that's why we're testing.
3. **Questions, not answers.** Frame goals as "Does X work for Y?" or "What happens
   when Z?" — never "X works because Y."
4. **Actions, not beliefs.** "What to Test" lists things to do, not things we think.
   Write "Try 30 DTE calls on mean-reversion dips" not "30 DTE is good for
   high-conviction plays."
5. **Let data speak.** Success criteria should be volume-based ("after N trades,
   compare results") not confirmation-based ("confirm that X works").

### For Rule Changes

- Modify the relevant section directly
- Keep rules concise and actionable
- Do not add assumptions or predictions to rules

## 4. Verify

Re-read the entry you wrote. Check each sentence against the no-assumptions rules.
If any sentence contains a prediction, assumed outcome, or conviction about what
works — rewrite it as a question or action.

## 5. Report

Post the change to Discord so the user can see what was added or modified.

## Guardrails

- This skill modifies ONLY `strategy/PAPER.md`
- Never modify experience files, skills, or toolkit code
- Never add assumptions, predictions, or convictions to the strategy
- When in doubt about whether something is an assumption, it is — rephrase it
