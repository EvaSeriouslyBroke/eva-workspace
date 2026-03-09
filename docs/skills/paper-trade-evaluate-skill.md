# Paper Trade Evaluate Skill

**Skill name**: `paper-trade-evaluate`
**Location**: `~/.openclaw/workspace/skills/paper-trade-evaluate/SKILL.md`

Eva's autonomous trading cycle — triggered by cron or on-demand. The most complex skill, involving strategy reading, data evaluation, news research, experience recall, and trade execution.

---

## Trigger Phrases

- "run paper trading evaluation"
- "evaluate paper trades"
- "check paper positions"
- Also triggered automatically by OpenClaw cron every 15 minutes during market hours

---

## SKILL.md Content

```yaml
---
name: paper-trade-evaluate
description: >
  Autonomous paper trading evaluation cycle. Triggered by cron every 15 minutes
  during market hours, or when asked to "run paper trading evaluation",
  "evaluate paper trades", "check paper positions".
metadata:
  openclaw:
    emoji: "🤖"
    requires:
      bins: ["python3"]
---
```

## Execution Flow

### 1. Load Context

1. Read `strategy/PAPER.md` — all trading rules

Do NOT read experiences yet — form your own assessment first.

### 2. Fetch Data

```bash
python3 {baseDir}/../../options-toolkit/eva.py evaluate --all
```

Parses as a JSON array (one object per ticker).

**Data guard:** Tradier sandbox data is 15 minutes delayed. Before ~9:45 AM ET, IV reads as 0% and quotes are unreliable. If `iv_context.current_avg_iv` is 0 or null, skip that ticker.

Use everything to form your initial idea:
- **Price action:** intraday OHLC, range position, recent daily candles, change percentages
- **All Greeks:** delta, gamma, theta, vega, rho — for every near-money option
- **IV context:** current IV, IV rank, IV percentile, 52-week IV high/low
- **Trends:** SMA 50/200 signals, returns (1w/1m/3m/6m/1y), 52-week price range
- **Volume & open interest:** per strike, put/call ratios
- **News headlines:** today's cached headlines with sentiment
- **Available expirations:** all expiries with DTE — look for short-term opportunities too

**News-price correlation:** Compare `news_history` (14 days) with `market_history` (14 days of price + IV + Greeks) side by side. Look for patterns: did a specific news event precede a price move? Did IV spike before or after news? This is how you learn from history without having to trade first.

### 3. Process Recently Closed Positions

If `recently_closed` contains positions with `needs_experience_update: true`:

1. Find or create the relevant experience file in `experience/`
2. Add evidence (supporting or contradicting) with today's date and `[paper]` tag
3. Update the Analysis section if understanding has deepened
4. Update `experience/INDEX.md` if a new file was created

### 4. Make Tentative Decisions

For each ticker, apply `PAPER.md` rules to the evaluation data. Possible actions: **sell**, **buy**, **double down**, or **hold**.

Write down each tentative decision with:
- The ticker and planned action
- The full situation: price move, IV level, all relevant Greeks, thesis
- What the news history and market history suggest (patterns you noticed)
- Key tags describing the pattern (e.g., mean-reversion, dip, earnings-gap, iv-spike, momentum, theta-decay, gamma-scalp, news-driven)

### 5. Deep News Research

For each ticker where you plan to **buy or double down**, run deep news research:

```bash
python3 {baseDir}/../../options-toolkit/eva.py news-research --ticker {TICKER} [--query "specific search"]
```

Use `--query` to search for what matters to your thesis. You can pass multiple `--query` flags to search for different angles. Examples:
- `--query "AAPL tariff impact"` — if tariffs are driving the move
- `--query "IWM earnings season small cap" --query "Russell 2000 outlook"` — multiple angles
- Omit `--query` entirely to use the default `"{TICKER} stock news"`

This fetches full article content — not just headlines. Read it carefully:
- Is there a fundamental reason behind the move? (earnings, acquisitions, regulatory, macro)
- Does the news support or contradict your thesis?
- Could this move continue based on what you're reading?

If the deep research contradicts your tentative decision, reconsider before proceeding. Include what you learned in your reasoning.

**Do NOT run news-research for holds** — only for actionable tickers.

### 6. Recall Experiences

Before executing, check your memory for similar past situations. Spawn an Agent (subagent_type: Explore) for each ticker where you plan to act (buy, sell, or double down — skip holds):

**Agent prompt:**
> Search Eva's trading experiences for situations similar to this:
>
> - **Ticker:** {TICKER}
> - **Planned action:** {buy call / buy put / sell / double down}
> - **Situation:** {1-2 sentence description of current conditions}
> - **Pattern tags:** {comma-separated tags}
>
> Steps:
> 1. Read `{baseDir}/../../experience/INDEX.md`
> 2. Find ALL experiences matching this ticker
> 3. Find general experiences AND experiences from other tickers with overlapping tags
> 4. Read each matching experience file
> 5. Return for each match: the file path, thesis, confidence level, key analysis points, recent evidence, and any exceptions/nuances relevant to this situation
> 6. If no experiences match, say so explicitly

You may launch multiple recall agents in parallel (one per ticker).

### 7. Final Verdict

Review deep news findings AND experience recall for each ticker:

- **News contradicts thesis:** Back out or adjust. Don't trade against fundamental moves.
- **Supporting experience (medium/high confidence):** Proceed with more conviction.
- **Contradicting experience:** Reconsider. The thesis may need adjustment or the trade may not be worth taking.
- **Disproven experience:** Do NOT repeat the same mistake. Adjust or skip.
- **No relevant experiences:** Proceed based on strategy rules and news research alone — this is a new pattern to learn from.

If news or recall changes your decision, explain why.

### 8. Execute

Buy:
```bash
python3 {baseDir}/../../options-toolkit/eva.py buy --ticker {TICKER} --type {call|put} --strike {STRIKE} --expiry {YYYY-MM-DD} --quantity 1 --reason "{DETAILED_REASONING}"
```

Sell:
```bash
python3 {baseDir}/../../options-toolkit/eva.py sell --ticker {TICKER} --type {call|put} --strike {STRIKE} --expiry {YYYY-MM-DD} --quantity 1 --reason "{DETAILED_REASONING}"
```

`--reason` must be detailed — it feeds `reasons.json` and the experience system. Include:
- What pattern you saw (price action, Greeks, IV, volume)
- What the news said (from deep research)
- What your experiences told you
- What the news-price history showed you
- Why you decided to proceed (or why you backed out of a tentative trade)

### 9. Report

- **Trade action:** `buy`/`sell` commands auto-send Discord notifications.
- **Experience update:** Post a brief note about what was learned.
- **Observational experience:** If you noticed a strong news-price pattern but didn't trade on it, you may create an experience file to remember it for next time.
- **Hold (no action):** Stay silent.

---

## Guardrails

- **NEVER call `reset`.** That command is user-only.
- All strategy rules live in `PAPER.md` — this skill only defines the process.
