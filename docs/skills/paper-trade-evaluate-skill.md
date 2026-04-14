# Paper Trade Evaluate Skill

**Skill name**: `paper-trade-evaluate`
**Location**: `~/.openclaw/workspace/skills/paper-trade-evaluate/SKILL.md`

Eva's autonomous day trading cycle — triggered by cron or on-demand. Involves strategy reading, direction determination, data evaluation, news research, experience recall, and trade execution. Experience *creation* is handled by the separate `paper-trade-reflect` skill.

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

**Time guard:** After 3:45 PM ET, do not open new positions. Only close existing ones.

Use everything to form your initial idea:
- **Market direction:** Is this a bull or bear environment? Check SMA 50/200 position, SPY context, RSI, recent daily candles, intraday momentum
- **Price action:** intraday OHLC, range position, recent daily candles, change percentages
- **All Greeks:** delta, gamma, theta, vega, rho — for every near-money option. Prefer high gamma for day trades.
- **IV context:** current IV, IV rank, IV percentile — high IV means expensive premiums
- **Trends:** SMA 50/200 signals, returns (1w/1m/3m/6m/1y), 52-week price range
- **Technical indicators:** RSI (overbought/oversold), ATR (volatility magnitude), Bollinger Bands (%B position)
- **Key levels:** previous day high/low (support/resistance)
- **Broader market:** SPY price, change %, trends — determine bull/bear backdrop
- **Volume:** intraday volume vs 50-day average — spot unusual activity
- **News headlines:** today's headlines with sentiment — catalysts for direction

**News-price correlation:** Compare `news_history` (14 days) with `market_history` (14 days of price + IV + Greeks) side by side. Look for patterns: did a specific news event precede a price move? Did IV spike before or after news?

**Deeper historical context:** When the 14-day `market_history` window isn't enough, use the `market-snapshots` skill.

### 3. Note Recently Closed

If `recently_closed` contains any entries, note them for context but do NOT create or update experience files here. The `paper-trade-reflect` skill handles experience updates in a separate session.

### 4. Determine Direction & Make Tentative Decisions

**Step 1: Market direction.** For each ticker, determine bull or bear:
- Price above 50 SMA + SPY green + positive momentum → **bull** → calls only
- Price below 50 SMA + SPY red + negative momentum → **bear** → puts only
- Mixed signals with reversal indicators → trade the direction stocks are **heading**

**Step 2: Open positions — close by EOD.** For each open position:
- **In profit?** Consider taking profits now. Day trades capture moves, not max gain.
- **Thesis invalidated?** Cut the loss immediately.
- **Near 3:30 PM?** Close everything regardless of P&L.
- **Direction reversed?** If your calls are in a stock now trending down (or puts trending up), exit.

**Step 3: New opportunities (buy).** Write down each tentative decision with:
- The ticker, direction (bull/bear), and planned action (buy call or buy put)
- Why this direction: what signals confirm it
- The intraday setup: what pattern you're trading
- Key tags describing the pattern (e.g., momentum, reversal, gap, news-driven, breakout, support-bounce)

### 5. Deep News Research

For each ticker where you plan to **buy**, run deep news research:

```bash
python3 {baseDir}/../../options-toolkit/eva.py news-research --ticker {TICKER} [--query "specific search"]
```

Use `--query` to search for what matters to your thesis. You can pass multiple `--query` flags to search for different angles.

This fetches full article content. Read it carefully:
- Does the news support your direction call (bull/bear)?
- Is there a catalyst that could drive an intraday move?
- Any risk of a reversal you haven't accounted for?

If the deep research contradicts your direction, reconsider.

**Do NOT run news-research for holds or closes** — only for new buys.

### 6. Recall Experiences

Before executing, check your memory for similar past situations. Spawn an Agent (subagent_type: Explore) for each ticker where you plan to buy:

**Agent prompt:**
> Search Eva's trading experiences for situations similar to this:
>
> - **Ticker:** {TICKER}
> - **Planned action:** {buy call / buy put}
> - **Direction:** {bull / bear / reversal}
> - **Situation:** {1-2 sentence description of current intraday conditions}
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

- **News contradicts direction:** Back out. Don't fight the news.
- **Supporting experience (medium/high confidence):** Proceed with more conviction.
- **Contradicting experience:** Reconsider. The setup may not work here.
- **No relevant experiences:** Proceed based on strategy rules and news alone — this is a new pattern to learn from.

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

`--reason` must be detailed — it feeds `reasons.json` and the experience system.

**For buys**, the reason IS the thesis. It must include:
- **Direction:** bull or bear, and the signals that confirm it
- **Setup:** what intraday pattern triggered the entry
- **Expected move:** what you think the stock/contract will do today
- **Invalidation:** what would prove the thesis wrong intraday
- **Exit plan:** when you plan to sell (target, time stop, by 3:30 PM)

**For sells**, the reason must explain:
- Why you're closing (profit target hit, thesis invalidated, direction reversed, EOD close)
- What the P&L outcome was
- What you learned from this trade

### 9. Report

- **Trade action:** `buy`/`sell` commands auto-send Discord notifications.
- **Hold (no action):** Stay silent.

---

## Guardrails

- **NEVER call `reset`.** That command is user-only.
- **NEVER hold overnight.** Close all positions by 3:45 PM ET.
- **Follow the direction rule.** Calls in bull markets, puts in bear markets. Only deviate when clear reversal signals appear.
- All strategy rules live in `PAPER.md` — this skill only defines the process.
