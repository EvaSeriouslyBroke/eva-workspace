# Paper Trade Hindsight Skill

**Skill name**: `paper-trade-hindsight`
**Location**: `~/.openclaw/workspace/skills/paper-trade-hindsight/SKILL.md`

Analyzes a single closed paper trade with hindsight — compares the sell decision against what actually happened, looks for rebuy opportunities, and identifies indicator signals. Runs per-symbol, dispatched by `run_hindsight.sh`.

---

## Trigger

Each invocation analyzes exactly ONE symbol, passed in the trigger message:
- `"Run hindsight analysis for NVDA260325C00190000"`

Can also be triggered on-demand:
- "run hindsight analysis for {SYMBOL}"
- "review the {SYMBOL} sell"
- "what if I held {SYMBOL}"

---

## Dispatch

`run_hindsight.sh` handles per-symbol dispatch:
1. Calls `eva.py hindsight --list` to get all closed watches
2. For each symbol, triggers an isolated agent session via `openclaw agent`
3. After all sessions are dispatched, runs `eva.py hindsight --clear-expired`

Runs via system crontab on Fridays at 4:15 PM ET.

---

## Execution Flow

### 1. Extract Symbol

Parse the OCC symbol from the trigger message.

### 2. Load Context

Read experience system docs and strategy rules.

### 3. Fetch Hindsight Data

```bash
python3 eva.py hindsight --symbol {SYMBOL}
```

Returns a single JSON object with the full trade lifecycle data.

### 4. Analyze the Trade

Five core questions:

1. **Sell timing** — was it right? Compare post-sale trajectory to sell decision.
2. **Better sell price** — were there peaks during the hold that were missed? What indicators signaled them?
3. **Rebuy opportunity** — did the option drop after the sell, creating a window to rebuy and resell?
4. **Indicator signals** — which technical indicators (RSI, Bollinger, IV, volume) predicted the post-sale moves?
5. **Luck vs skill** — was the outcome driven by predictable patterns or unpredictable events?

### Data Available

- **Pre-sale analysis** — option trajectory during the hold, peak/trough with dates and P&L, stock price at those moments
- **Hold-period stock context** — daily OHLCV + indicators (RSI, ATR, Bollinger, SMAs) at entry, option peak, option trough, sell
- **Entry/sell market context** — full snapshots at both entry and exit with trends, IV context, broader market
- **Daily trajectory** — day-by-day post-sale option OHLC, IV, delta, theta, stock OHLC + volume
- **Stock context** — post-sale stock trajectory + indicators at key dates
- **Key moment snapshots** — full Greeks/IV/prices at peak, trough, boundaries
- **Counterfactual** — realized P&L vs hold-to-now, peak/trough values, missed upside, avoided downside
- **News/market around key dates** — headlines and stock/IV environment near sell, peak, trough

### 5. Update Experiences

Add `[hindsight]` evidence entries focused on sell timing, rebuy opportunities, and indicator signals.

### 6. Propose Tests

If the analysis reveals a testable hypothesis, add it to PAPER.md's Testing section.

### 7. Report

Post Discord summary of the single trade's findings.

---

## Guardrails

- Does NOT make trading decisions
- Does NOT run `evaluate`, `buy`, or `sell`
- Focus only on hindsight analysis, experience updates, and proposing tests

---

## CLI Flags

| Flag | Description |
|------|-------------|
| `--symbol X` | Analyze a specific OCC symbol |
| `--list` | List symbols awaiting hindsight analysis (no API calls) |
| `--expired-only` | Only show expired contracts |
| `--clear-expired` | Remove expired contracts and watches >30 days past sell |
