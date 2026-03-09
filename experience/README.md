# Experience System

Eva's thesis-based learning system for paper trading. Each experience is a living document that evolves as trades confirm or contradict its thesis.

## How Experiences Are Used

Eva recalls experiences **after** forming a tentative decision — like a human thinking "have I seen this before?" She spawns a recall agent that searches INDEX.md by ticker and pattern tags, reads matching files, and returns findings. Eva then confirms, adjusts, or reverses her decision based on past evidence.

## Structure

```
experience/
├── README.md          ← You are here
├── INDEX.md           ← Lookup table: one-line summaries, tags, confidence
├── general/           ← Market-wide patterns (e.g., "IV crush after earnings")
└── tickers/           ← Ticker-specific patterns (e.g., "IWM mean-reverts after 3%+ drops")
    └── {TICKER}/      ← Created as needed
```

## Experience File Format

Each `.md` file in `general/` or `tickers/{TICKER}/` follows this structure:

```markdown
# {Title}

**Thesis:** {One-sentence claim}
**Applies to:** {Ticker(s) or "general"}
**Tags:** {comma-separated}
**Confidence:** {low | medium | high | disproven}
**Last Updated:** {YYYY-MM-DD}

## Analysis

{Current understanding. Rewritten as it deepens — not appended to.}

## Evidence

### Summary
{X supporting, Y contradicting observations total.}
{One-paragraph digest of older evidence — key patterns, notable outliers.}

### Recent
- {YYYY-MM-DD} [supporting]: {What happened and why}
- {YYYY-MM-DD} [contradicting]: {What happened and why}

## Exceptions & Nuances

- {Conditions where the thesis doesn't apply}
```

## Evidence Management

Keep the **5 most recent** entries detailed in the Recent section. When adding a 6th, roll the oldest entry into the Summary paragraph and update the counts. Summary should capture the gist — don't lose important outliers or turning points, but don't keep every line item.

## Evolution Rules

1. **New pattern observed** → create experience file, add to INDEX.md
2. **Supporting trade** → add recent evidence entry, optionally strengthen confidence
3. **Contradicting trade** → add recent evidence, analyze why, update Analysis, add Exceptions
4. **Proven wrong** → set confidence to "disproven", explain why in Analysis — never delete
5. **Observational pattern** → spotted in news_history + market_history correlation without trading → create experience with `[observed]` tag in evidence
6. **Analysis section** gets rewritten (not appended) as understanding deepens
7. **Evidence** stays compact — recent entries are detailed, older ones are summarized with counts
