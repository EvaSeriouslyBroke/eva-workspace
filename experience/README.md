# Experience System

Eva's thesis-based learning system for paper trading. Each experience is a living document that evolves as trades confirm or contradict its thesis.

## How Experiences Are Used

Eva recalls experiences **after** forming a tentative decision — like a human thinking "have I seen this before?" She spawns a recall agent that searches INDEX.md by ticker and pattern tags, reads matching files, and returns findings. Eva then confirms, adjusts, or reverses her decision based on past evidence.

Experience *creation* is handled by the `paper-trade-reflect` skill in a separate session. When positions close, the data is persisted to `pending_experience_updates.json` and the reflect skill processes it ~7 minutes later.

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
**Tags:** {comma-separated — MUST include a regime tag and a DTE bucket tag}
**Confidence:** {low | medium | high | disproven}
**Last Updated:** {YYYY-MM-DD}

## Analysis

{Current understanding. Rewritten as it deepens — not appended to.}

## Evidence

### Summary
{X supporting, Y contradicting observations total.}
{One-paragraph digest of older evidence — key patterns, notable outliers.}

### Recent
- {YYYY-MM-DD} [paper] [supporting] [bear] [dte-short]: {What happened and why}
- {YYYY-MM-DD} [paper] [contradicting] [bull] [dte-medium]: {What happened and why}
- {YYYY-MM-DD} [hindsight] [supporting] [bear] [dte-short]: {Post-sale analysis insight}
- {YYYY-MM-DD} [observed]: {Pattern spotted in data without trading}

## Exceptions & Nuances

- {Conditions where the thesis doesn't apply}
```

## Evidence Management

`[supporting]` and `[contradicting]` tags are relative to the **experience file's thesis**, not the original trade thesis. When the thesis is rewritten (especially inverted), re-tag all existing evidence entries and update the summary counts to match the new thesis direction.

Keep the **5 most recent** entries detailed in the Recent section. When adding a 6th, roll the oldest entry into the Summary paragraph and update the counts. Summary should capture the gist — don't lose important outliers or turning points, but don't keep every line item.

## Required Tags

Every experience MUST include a **market regime** tag and a **DTE bucket** tag. These go in both the file-level Tags field and on each evidence entry.

### Market Regime (at trade entry)

| Tag | Meaning |
|-----|---------|
| `bull` | Broad market in uptrend (above key SMAs, positive trajectory) |
| `bear` | Broad market in downtrend (below key SMAs, negative trajectory) |
| `transition` | Market shifting between regimes (mixed signals, turning points) |
| `unclear` | No clear regime signal |

### DTE Bucket (at trade entry)

| Tag | DTE Range |
|-----|-----------|
| `dte-short` | **< 45 DTE** |
| `dte-medium` | **45–90 DTE** |
| `dte-long` | **> 90 DTE** |

These tags prevent conflating patterns that work in one regime/timeframe but fail in another. When evidence accumulates across regimes, an experience may split into regime-specific files (e.g., one for bull, one for bear) if the pattern behaves differently.

## Evolution Rules

1. **New pattern observed** → create experience file with required tags, add to INDEX.md
2. **Supporting trade** → add recent evidence entry, optionally strengthen confidence
3. **Contradicting trade** → add recent evidence, analyze why, update Analysis, add Exceptions
4. **Regime-dependent behavior** → if contradicting evidence comes from a different regime, consider splitting into separate regime-specific experience files rather than weakening confidence
5. **Proven wrong** → set confidence to "disproven", explain why in Analysis — never delete
6. **Observational pattern** → spotted in news_history + market_history correlation without trading → create experience with `[observed]` tag in evidence
7. **Analysis section** gets rewritten (not appended) as understanding deepens
8. **Evidence** stays compact — recent entries are detailed, older ones are summarized with counts

## Confidence Levels

- **low** — initial observation, 1-2 trades, pattern may be coincidence
- **medium** — confirmed across multiple independent conditions (different market days, different setups, or different timeframes). Requires substantial evidence, not just repeated trades from the same play or timeline.
- **high** — strong track record with clear causal understanding. Multiple confirming trades across varied conditions.
- **disproven** — evidence shows the thesis is wrong. Kept to avoid re-learning.

**Do not upgrade confidence** based on:
- Multiple trades from the same day or the same decision (e.g., a buy and a double-down are one play, not two independent data points)
- Trades that share the same entry thesis and market conditions — they're correlated, not independent
- A small number of observations that all happened in the same market regime

Confidence upgrades require evidence from **different occasions** — separated by time, market conditions, or setup variations.
