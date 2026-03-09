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

Lookup table for the experience recall agent. One-line summaries with tags so it can quickly find relevant files by ticker and pattern. Organized by section (General, then per-ticker). Does not duplicate confidence — the agent reads the actual file for that.

## Evolution Lifecycle

1. **New pattern observed** → create experience file + add to INDEX.md
2. **Supporting trade** → add evidence entry, optionally strengthen confidence
3. **Contradicting trade** → add evidence, analyze why, update Analysis, add Exceptions
4. **Pattern becomes clear** → rewrite Analysis with deeper understanding
5. **Thesis proven wrong** → set confidence to "disproven", explain why — never delete
6. **Observational pattern** → Eva spots a news→price correlation in history data without having traded on it — creates an experience to remember for next time

Disproven theses are kept to prevent re-learning the same wrong lesson. Observational experiences let Eva learn from history without requiring firsthand trades.

## Confidence Levels

- **low** — initial observation, 1-2 trades, pattern may be coincidence
- **medium** — confirmed across multiple independent conditions (different market days, different setups, or different timeframes). Requires substantial evidence.
- **high** — strong track record with clear causal understanding across varied conditions.
- **disproven** — evidence shows the thesis is wrong. Kept to avoid re-learning.

**Do not upgrade confidence** based on correlated trades — multiple trades from the same day, the same decision (a buy + double-down is one play), or the same market conditions. Confidence upgrades require evidence from **different occasions** separated by time, conditions, or setup variations.

## Evidence Management

`[supporting]` and `[contradicting]` tags are relative to the **experience file's thesis**, not the original trade thesis. When the thesis is rewritten (especially inverted), re-tag all existing evidence entries and update the summary counts to match the new thesis direction.

Keep the **5 most recent** entries detailed in the Recent section. When adding a 6th, roll the oldest into the Summary paragraph and update the counts. Summary captures the gist — important outliers and turning points are preserved, but individual line items are not.

## Integration with Paper Trading

### Writing Experiences

- **From trades:** The `sell` command immediately writes closed position data to `pending_experience_updates.json` (with entry context, snapshots, and reasoning). For expirations, `detect_recently_closed` in the evaluate cycle handles detection. The `paper-trade-reflect` skill (running ~7 min after each evaluate cycle) reads this file, creates/updates experience files, then clears the pending file. Evidence entries include date, mode tag (`[paper]`/`[real]`), and description.
- **From observations:** Eva can create experience files from patterns noticed in `news_history` and `market_history` data (14 days each) without having traded. For example, noticing that tariff news consistently precedes a 2-day IWM dip. These observational experiences use the same file format but note `[observed]` in evidence entries.

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
