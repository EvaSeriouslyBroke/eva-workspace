# summary Command — End-of-Day Summary

Generates an end-of-day summary comparing market open to close, with technical and market-based analysis.

---

## Usage

```
python3 eva.py summary --ticker IWM [--force]
```

### Flags

| Flag | Required | Description |
|------|----------|-------------|
| `--ticker <SYM>` | Yes | Ticker symbol |
| `--force` | No | Skip schedule check (runs at any time) |

---

## Schedule Guard

Without `--force`, the summary only runs at **4:01 PM ET** (`SUMMARY_SCHEDULE = [(16, 1)]`). At all other times it exits silently (code 0, no output).

---

## What It Does

1. Loads **all snapshots from today** (`load_today_snapshots()`)
2. Finds the first snapshot with valid IV (>= 1%) — skips early-morning snapshots where IV reads as 0%
3. Compares that first valid snapshot with the last snapshot of the day
4. Computes intraday ranges for price, IV, volume, OI, and skew
5. Generates technical analysis (rules-based) and market assessment
6. Outputs a day rating (BULLISH / SLIGHTLY BULLISH / NEUTRAL / SLIGHTLY BEARISH / BEARISH)

Requires at least 2 snapshots from today with at least one having valid IV (>= 1%). If these conditions aren't met, exits silently.

---

## Output Format (3 Chunks with `---SPLIT---`)

### Chunk 1: Header + Price Action

```
========================================
  📊 IWM END-OF-DAY SUMMARY
========================================

📅 2026-03-04 | Market Close

Price Action:
  Open: $208.00 → Close: $211.25
  Day Change: +$3.25 (+1.56%) 🟢
  Day Range: $207.50 - $211.80
  Snapshots: 6
```

### Chunk 2: Intraday Metrics

```
📈 INTRADAY METRICS
────────────────────────────────────────

Implied Volatility:
  Open IV: 25.30% → Close IV: 24.80%
  IV Change: -0.50% 🟢
  IV Range: 24.20% - 26.10%
  Call IV: 24.50% → 24.10%
  Put IV: 26.10% → 25.50%

Volume:
  P/C Vol Ratio: 1.05 → 0.84

Open Interest:
  P/C OI Ratio: 0.87 → 0.86

Skew:
  Open: +1.80% → Close: +1.20%
  Skew Change: -0.60%
```

### Chunk 3: Analysis

```
🔍 END-OF-DAY ANALYSIS
────────────────────────────────────────

Technical:
  • IV contracted — volatility sellers dominated
  • P/C vol ratio < 0.8 — call-heavy flow
  • P/C OI ratio declining — call OI gaining vs puts
  • Skew narrowing — put premium declining

Market Assessment:
  • Price up + IV down = healthy rally with confidence
  • Volume sentiment shifted bullish through the day
  • Significant move (+1.56%) — high conviction day

Day Rating: BULLISH 🟢

========================================
✅ END-OF-DAY SUMMARY COMPLETE
========================================
```

---

## Technical Analysis Rules

| Metric | Condition | Interpretation |
|--------|-----------|----------------|
| IV Change | < -1% | "IV contracted — volatility sellers dominated" |
| IV Change | > +1% | "IV expanded — increased uncertainty/fear" |
| IV Change | between | "IV stable — no significant volatility shift" |
| P/C Vol Ratio | < 0.8 | "call-heavy flow" |
| P/C Vol Ratio | > 1.2 | "put-heavy flow" |
| P/C Vol Ratio | between | "balanced" |
| P/C OI Ratio Change | < -0.05 | "call OI gaining vs puts" |
| P/C OI Ratio Change | > +0.05 | "put OI gaining vs calls" |
| P/C OI Ratio Change | between | "stable" |
| Skew Change | < -0.5 | "put premium declining" |
| Skew Change | > +0.5 | "protection demand rising" |

## Market Assessment Rules

| Price | IV | Interpretation |
|-------|----|----------------|
| Up | Down | "healthy rally with confidence" |
| Up | Up | "rally with hedging demand" |
| Down | Up | "fear-driven selling" |
| Down | Down | "orderly pullback" |
| Flat | Flat | "minimal directional commitment" |

Additional signals:
- P/C vol ratio shifted down > 0.1: "sentiment shifted bullish"
- P/C vol ratio shifted up > 0.1: "sentiment shifted bearish"
- Price change > 1%: "high conviction day"
- Price change < 0.2%: "indecision/consolidation"

## Day Rating Score

5 independent scoring factors (each can contribute +1 or -1, range -5 to +5):
- Price direction (up +1, down -1)
- IV direction (down +1, up -1)
- P/C vol ratio level (< 0.9 +1, > 1.1 -1)
- P/C OI ratio change (< -0.05 +1, > +0.05 -1)
- Skew change (< -0.3 +1, > +0.3 -1)

| Score | Rating |
|-------|--------|
| >= 3 | BULLISH 🟢 |
| 1-2 | SLIGHTLY BULLISH 🟢 |
| 0 | NEUTRAL 🟡 |
| -1 to -2 | SLIGHTLY BEARISH 🔴 |
| <= -3 | BEARISH 🔴 |
