# Experience System

Eva's thesis-based learning system. Each experience is a living document that evolves as trades confirm or contradict its thesis.

## Directory Structure

```
experience/
├── README.md              ← How the system works
├── INDEX.md               ← Lookup table for experience recall
├── general/               ← Market-wide patterns
│   └── (created by Eva)
└── tickers/               ← Ticker-specific patterns
    └── {TICKER}/          ← Created per ticker as needed
```

## File Format

Each experience file is a thesis with:
- **Thesis** — one-sentence core claim
- **Applies to** — general or specific ticker
- **Tags** — for index lookup
- **Confidence** — low / medium / high / disproven
- **Analysis** — current best understanding (rewritten as it deepens, never appended)
- **Evidence** — Summary (counts + digest of older evidence) + Recent (up to 5 detailed entries, tagged `[paper]` or `[real]`)
- **Exceptions & Nuances** — conditions where the thesis doesn't hold

## INDEX.md

Lookup table for the experience recall agent. One-line summaries with tags so it can quickly find relevant experiences by ticker and pattern. Organized by section (General, then per-ticker).

## Evolution Lifecycle

1. **New pattern observed** → create experience file + add to INDEX.md
2. **Supporting trade** → add evidence entry, optionally strengthen confidence
3. **Contradicting trade** → add evidence, analyze why, update Analysis, add Exceptions
4. **Pattern becomes clear** → rewrite Analysis with deeper understanding
5. **Thesis proven wrong** → set confidence to "disproven", explain why — never delete

Disproven theses are kept to prevent re-learning the same wrong lesson.

## Evidence Management

Keep the **5 most recent** entries detailed in the Recent section. When adding a 6th, roll the oldest into the Summary paragraph and update the counts. Summary captures the gist — important outliers and turning points are preserved, but individual line items are not.

## Integration with Paper Trading

### Writing Experiences

- The `evaluate` command outputs `recently_closed` with `needs_experience_update: true`
- The `paper-trade-evaluate` skill checks for recently closed positions before making new decisions
- Eva updates experience files, then proceeds with evaluation
- Evidence entries include date, mode tag (`[paper]`/`[real]`), and description

### Recalling Experiences

Eva recalls experiences **after** forming a tentative decision, not before. This prevents anchoring bias — she assesses the market fresh, then checks memory.

The recall flow:
1. Eva makes a tentative decision based on strategy rules + market data
2. For each planned action (buy/sell/double down), Eva spawns a subagent to search experiences
3. The subagent reads INDEX.md, finds matching experiences by ticker AND by pattern tags across all tickers/general
4. Eva reviews the findings and confirms, adjusts, or reverses her decision
5. Experience findings are included in the trade's `--reason`

This mirrors human memory — assess the situation first, then think "have I seen this before?"

## Who Writes Experiences

Eva writes experiences through the LLM (not code) because categorization, analysis, and thesis refinement require judgment. The `experience/` directory is outside AGENTS.md restricted paths.
