# Paper Trading System for Eva (Tradier Sandbox)

## Vision

Eva learns to trade through two modes that run simultaneously:

- **Paper trading** (sandbox) — experimental, frequent, builds the experience knowledge base. Uses Tradier sandbox API with 15-minute delayed data. Trades reported to `paper-trading` Discord channel.
- **Real trading** (live) — conservative, infrequent, only acts on proven theses. Uses Tradier live API with real-time data. Trades reported to `real-trading` Discord channel. **Not implemented yet.**

Both modes feed into the **same experience system**. Paper and real evidence carry equal weight — the 15-minute delay doesn't meaningfully affect pattern recognition. Evidence is tagged `[paper]` or `[real]` for audit purposes, not for weighting.

**Data isolation is critical.** Paper trading uses sandbox API exclusively. Real trading (when added) uses live API exclusively. Market data, quotes, and chains are never shared between modes. This prevents delayed sandbox data from contaminating real-time decisions.

**This plan implements paper trading only.** The architecture is mode-aware from day one so real trading plugs in cleanly later.

## Context

Eva currently analyzes options (IV, chains, news, reports) but doesn't trade. The goal is to add autonomous paper trading using **Tradier's sandbox API** — a real broker's paper trading environment. Eva will reason about trades every 15 minutes and build an experience knowledge base to improve over time.

Key decisions:
- **Tradier sandbox** for everything (market data + trade execution + portfolio)
- **$100,000 starting capital** (Tradier sandbox default, not configurable)
- **Cash account** — funds from closed trades take 1 day to settle before they're usable again. Eva must track settled vs unsettled cash when deciding what she can afford.
- **Simple long only** — buy calls, buy puts (buy_to_open / sell_to_close)
- **Autonomous every 15 mins** via OpenClaw agent so Eva reasons about each decision
- **Dedicated Discord channel** — `paper-trading` channel
- **Baseline strategy included** — mean reversion with news filter, 120+ DTE, lean toward trading more during sandbox phase
- **Market orders only** — simpler execution, but Eva should understand fill price may differ slightly from the quote she saw
- **Experience knowledge base** — living theses (general + ticker-specific), refined over time. Evidence grows endlessly (bad theses are kept as "Disproven" to prevent re-learning mistakes)

---

## What Tradier Handles vs What We Build

**Tradier sandbox API handles:**
- Portfolio state (cash balance, equity, market value)
- Open positions (with cost basis, current value, P&L)
- Order execution (realistic fills, order status tracking)
- Order history (filled, canceled, expired)
- Market data (quotes, option chains with greeks/IV, expirations, strikes)

**We build:**
- `paper_trading.py` — Mode-aware CLI wrapper around Tradier API with formatted output for Discord
- Trade reasoning log — Tradier doesn't store "why" Eva made a trade; the `buy`/`sell` commands capture reasoning at trade time
- Evaluation logic — what data to pull, how to present it for Eva's decision-making
- Experience knowledge base — lessons learned, organized by situation type
- Closed position detection — check for recently closed trades and trigger experience reflection
- Skills — OpenClaw skill definitions for autonomous + interactive use

---

## Tradier API Reference

**Sandbox base URL:** `https://sandbox.tradier.com/v1`
**Live base URL:** `https://api.tradier.com/v1` (future — not used yet)
**Auth header:** `Authorization: Bearer <TOKEN>`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/accounts/{id}/balances` | GET | Cash, equity, market value |
| `/accounts/{id}/positions` | GET | Open positions with P&L |
| `/accounts/{id}/orders` | GET | Order history |
| `/accounts/{id}/orders` | POST | Place order |
| `/accounts/{id}/orders/{oid}` | DELETE | Cancel order |
| `/markets/quotes?symbols=IWM` | GET | Stock quote |
| `/markets/options/chains?symbol=IWM&expiration=DATE&greeks=true` | GET | Option chain with IV, greeks |
| `/markets/options/expirations?symbol=IWM` | GET | Available expiration dates |
| `/markets/options/strikes?symbol=IWM&expiration=DATE` | GET | Available strikes |
| `/markets/history?symbol=IWM&interval=daily&start=DATE&end=DATE` | GET | Daily OHLCV price history |

**OCC option symbol format:** `IWM260630C00265000` = IWM, Jun 30 2026, Call, $265 strike

**Option order params:** `class=option, symbol=IWM, option_symbol=IWM260630C00265000, side=buy_to_open|sell_to_close, quantity=1, type=market, duration=day`

**Rate limits:** 60 requests/min (sandbox), 120 requests/min (live). At 15-min eval intervals with ~6 calls per ticker, this is well within limits even for multiple tickers.

---

## Implementation Plan

### Step 1: Tradier Config

**File:** `~/.openclaw/workspace/options-toolkit/tradier.json`

```json
{
  "paper": {
    "token": "<USER_PROVIDES>",
    "account_id": "<USER_PROVIDES>",
    "base_url": "https://sandbox.tradier.com/v1"
  }
}
```

When real trading is added later, a `"real"` key gets added with live credentials. The script reads the appropriate section based on `--mode`.

This stays out of version control. Eva reads it but never modifies it.

### Step 2: Create `paper_trading.py` — Tradier API Client + CLI

**File:** `~/.openclaw/workspace/options-toolkit/paper_trading.py` (~500-600 lines)

Standalone Python script. Only dependency: `requests` (standard for HTTP). No yfinance, no imports from toolkit.py.

**Mode-aware from day one.** Every command accepts `--mode paper|real` (defaults to `paper`). The mode determines which Tradier credentials, base URL, data directory, and Discord channel to use. For now, only `paper` is implemented — passing `--mode real` exits with an error.

**Subcommands:**

| Command | Purpose | Tradier API Used |
|---------|---------|-----------------|
| `evaluate --ticker X [--force]` | Build evaluation JSON for Eva to reason about | balances + positions + chains + quotes + history |
| `status` | Formatted portfolio for Discord | balances + positions + orders |
| `buy --ticker X --type call\|put --strike N --expiry DATE [--quantity 1] --reason "..."` | Place buy_to_open order, log reasoning | POST orders + quotes |
| `sell --ticker X --type call\|put --strike N --expiry DATE [--quantity 1] --reason "..."` | Place sell_to_close order, log reasoning | POST orders |
| `history [--limit N]` | Show recent orders with reasoning | GET orders + local reasons |
| `reset --confirm` | Cancel all orders, close all positions, archive local logs. **User-only, never autonomous.** | DELETE orders + POST sell_to_close for each position |

**Error handling:**
- All Tradier API calls wrapped with retry (3 attempts, exponential backoff)
- Non-200 responses logged with full context and produce a clear error message
- Timeout after 10 seconds per request
- On failure during `evaluate`: output partial data with error flags so Eva knows what's missing
- On failure during `buy`/`sell`: never silently fail — always report the error

**`evaluate` output** (JSON for Eva to reason about):
```json
{
  "timestamp": "2026-03-05T10:15:00-05:00",
  "mode": "paper",
  "ticker": "IWM",
  "account": {
    "cash": 847.50,
    "unsettled_funds": 152.00,
    "settled_cash": 695.50,
    "market_value": 1010.00,
    "total_equity": 1010.00
  },
  "positions": [
    {
      "symbol": "IWM260630C00265000",
      "type": "call", "strike": 265, "expiry": "2026-06-30", "dte": 117,
      "quantity": 1, "cost_basis": 152.00,
      "current_bid": 1.60, "current_ask": 1.65,
      "market_value": 162.50, "unrealized_pnl": 10.50, "pnl_pct": 6.9,
      "entry_context": {
        "reason": "Mean reversion — IWM dipped 3% on tariff fears, expecting recovery",
        "entry_price": 258.30, "entry_iv": 26.1, "entry_date": "2026-02-28",
        "price_change_since_entry_pct": 1.5
      }
    }
  ],
  "recently_closed": [
    {
      "symbol": "IWM260630P00255000",
      "type": "put", "strike": 255, "expiry": "2026-06-30",
      "quantity": 1, "cost_basis": 120.00, "proceeds": 85.00,
      "realized_pnl": -35.00, "pnl_pct": -29.2,
      "open_reason": "Mean reversion — IWM dipped on tariff fears",
      "close_reason": "Thesis wrong — tariff impact was fundamental",
      "closed_how": "sell_to_close",
      "needs_experience_update": true
    }
  ],
  "market": {
    "price": 262.10, "change_pct": 1.14,
    "trends": {
      "price_52w_high": 232.86,
      "price_52w_low": 196.80,
      "price_vs_52w_pct": 38,
      "sma_50": 210.15,
      "sma_200": 218.40,
      "sma_signal": "below_both",
      "returns": { "1w": -2.1, "1m": -5.3, "3m": -12.1, "6m": -8.7, "1y": -15.2 },
      "trend_summary": "Downtrend — below 50 and 200 SMA, down 15% over 12 months"
    },
    "chain_summary": {
      "near_money_calls": ["..."],
      "near_money_puts": ["..."],
      "avg_call_iv": 24.5, "avg_put_iv": 26.1,
      "pc_vol_ratio": 0.85
    }
  },
  "affordable_options": [
    { "symbol": "IWM260630C00270000", "type": "call", "strike": 270,
      "expiry": "2026-06-30", "dte": 117, "bid": 0.95, "ask": 1.05,
      "iv": 28.3, "delta": 0.25, "cost": 105.00 }
  ],
  "experience_context": "Read experience/INDEX.md to find relevant experiences"
}
```

Key details:
- `affordable_options` filters to options where `ask * 100 <= settled_cash` (only settled funds are usable in a cash account)
- `recently_closed` shows positions closed since last evaluation — triggers experience reflection
- `experience_context` points Eva to the experience index
- `entry_context` on each position gives Eva the original thesis and market conditions at entry, so she can judge whether her thesis is playing out
- Market hours guard: silent exit outside 9:30-16:00 ET Mon-Fri unless `--force`
- Reads from Tradier for everything (no yfinance)
- `mode` field included so Eva always knows which mode she's operating in
- Market orders only — fill price may differ from quoted price

**Duplicate trade prevention:** Before placing a buy order, check if an identical position already exists (same ticker, type, strike, expiry). If so, skip and log why.

**Closed position detection lifecycle:**
1. `buy` command writes the position to `known_positions.json` (symbol, entry context, order ID)
2. Each `evaluate` call diffs `known_positions.json` against Tradier's current positions
3. Positions in `known_positions.json` but NOT in Tradier = closed (sold, expired, or assigned)
4. Closed positions appear in `recently_closed` with `closed_how` (sell_to_close, expired, unknown)
5. After Eva reflects and updates experiences, the evaluate skill marks the position as "reflected" in `known_positions.json`
6. Reflected positions no longer appear in `recently_closed`
7. Expiration detection: if a position disappears and there's no sell order, it expired worthless

**Settlement note:** If Tradier sandbox doesn't simulate settlement (i.e., `unsettled_funds` is always 0), the script reports all cash as settled. The constraint becomes real when live trading is added. Verify during implementation.

**`status` output** (formatted for Discord):
```
========================================
  💰 EVA'S PAPER TRADING PORTFOLIO
========================================

💵 Cash: $847.50
📊 Portfolio Value: $1,010.00
📈 Total Equity: $1,010.00

📋 OPEN POSITIONS (1)
────────────────────────────────────────
IWM $265 Call — Jun 30 (117 DTE)
  Cost: $152.00 | Value: $162.50
  P&L: +$10.50 (+6.9%) 🟢

📊 TODAY'S ORDERS
────────────────────────────────────────
✅ BUY IWM $265C Jun30 — Filled @ $1.52
```

**Local data** (per mode, only what Tradier doesn't store):

```
data/paper-trading/
├── reasons.json       # Maps Tradier order IDs to Eva's reasoning
├── known_positions.json  # Tracks positions for closed-trade detection
└── log.jsonl          # Structured event log for debugging
```

```json
// reasons.json
{
  "12345": {
    "reason": "IV contracting with bullish P/C ratio shift; news positive on small-cap rotation",
    "timestamp": "2026-03-05T09:30:00-05:00",
    "market_context": { "iv": 24.5, "price": 261.56, "pc_ratio": 0.85 }
  }
}
```

```jsonl
// log.jsonl — append-only structured log
{"ts": "2026-03-05T09:30:00", "event": "evaluate", "ticker": "IWM", "result": "buy_signal"}
{"ts": "2026-03-05T09:30:01", "event": "order_placed", "order_id": "12345", "side": "buy_to_open", "symbol": "IWM260630C00265000"}
{"ts": "2026-03-05T09:30:02", "event": "api_error", "endpoint": "/markets/quotes", "status": 429, "retry": 1}
```

When real trading is added: `data/real-trading/` with the same structure. Data dirs never overlap.

**`reset` archives before clearing.** Copies `reasons.json` to `reasons.YYYY-MM-DD.json` before wiping.

### Step 3: Create Experience System

**Directory:** `~/.openclaw/workspace/experience/`

The experience system is a **living knowledge base**, not a trade journal. Each experience file is a **thesis** about how markets behave, refined over time as Eva gathers evidence. The Analysis section gets rewritten as understanding deepens, but evidence entries grow endlessly — every trade result is kept. Disproven theses are never deleted, only marked as "Disproven" to prevent Eva from re-learning the same wrong lesson.

**Two categories:**
- **General** (`experience/general/`) — patterns that apply across all stocks
- **Ticker-specific** (`experience/tickers/{TICKER}/`) — patterns unique to one stock

**Structure:**
```
experience/
├── README.md              # How the experience system works
├── INDEX.md               # Searchable index — Eva reads this FIRST
├── general/
│   └── (created by Eva as she learns)
└── tickers/
    └── (created by Eva per ticker as she learns)
```

**INDEX.md** — Eva's lookup table. One-line summaries with tags so she can quickly find relevant experiences:
```markdown
# Experience Index

## General
- **[bad-news-recovery](general/bad-news-recovery.md)** — Stocks often recover 2-3 days after bad news if fundamentals unchanged. Tags: news, recovery, dip-buy, timing. Confidence: medium.
- **[iv-crush-post-event](general/iv-crush-post-event.md)** — IV collapses after known events regardless of direction. Tags: IV, events, volatility. Confidence: high.

## IWM
- **[tariff-sensitivity](tickers/IWM/tariff-sensitivity.md)** — IWM drops sharply on tariff news, recovers slowly. Tags: tariffs, small-cap, news. Confidence: medium.

## AMD
- **[downtrend-on-good-news](tickers/AMD/downtrend-on-good-news.md)** — AMD tends to trend down even on positive earnings/news. Tags: counter-intuitive, earnings. Confidence: low.
```

**Individual experience file format** — a living thesis, not a log:
```markdown
# [Thesis Title]

**Thesis:** [Core claim — 1-2 sentences. This is the experience.]
**Applies to:** General | {TICKER}
**Tags:** [comma-separated for index lookup]
**Confidence:** Low | Medium | High
**Last Updated:** YYYY-MM-DD

## Analysis

[The reasoning behind this thesis. Market mechanics, observed patterns,
why Eva believes this. This section gets REWRITTEN as understanding
deepens — not appended to. Should read as current best understanding.]

## Evidence

### Supporting
- YYYY-MM-DD [paper|real]: [What happened that supports this thesis]
- YYYY-MM-DD [paper|real]: [Another supporting observation]

### Contradicting
- YYYY-MM-DD [paper|real]: [What happened that contradicts. Why? Was it a different
  condition? An exception? This analysis refines the thesis.]

## Exceptions & Nuances

- [Conditions where this thesis does NOT hold]
- [Important caveats discovered through contradicting evidence]
```

**How experiences evolve:**
1. **New pattern observed** → Eva creates a new experience file + adds to INDEX.md
2. **Trade supports thesis** → Add to Supporting evidence, maybe bump Confidence
3. **Trade contradicts thesis** → Add to Contradicting, analyze why, update Analysis section, add Exceptions. Maybe modify the Thesis itself.
4. **Pattern becomes clear** → Rewrite Analysis with deeper understanding
5. **Thesis proven wrong** → Don't delete. Lower Confidence to "Disproven", explain why in Analysis. This prevents Eva from re-learning the same wrong lesson.

**No pre-created template files.** Eva starts with an empty knowledge base and builds it organically as she trades. The README.md and INDEX.md are the only starter files.

Eva writes/updates experiences through the LLM (not code) because categorization, analysis, and thesis refinement require judgment. The `experience/` directory is outside AGENTS.md restricted paths, so Eva has write access.

### Step 4: Create Skills (3 new)

**`skills/paper-trade-evaluate/SKILL.md`** — Autonomous. Triggered by OpenClaw cron every 15 min. Instructions:
1. Read `strategy/PAPER.md` + `experience/INDEX.md` before every decision
2. Read `tickers.json` — evaluate each ticker in the list
3. Run `paper_trading.py evaluate --ticker X` for each ticker
4. **Check `recently_closed`** — if any trades closed, update relevant experience files FIRST
5. Analyze evaluation output, decide buy/sell/hold per ticker
6. If buying: `paper_trading.py buy --ticker X --type call --strike N --expiry DATE --reason "..."`
7. If selling: `paper_trading.py sell --ticker X --type call --strike N --expiry DATE --reason "..."`
8. Post to Discord `paper-trading` channel (only on action or experience update; most HOLD cycles are silent)

Tickers are managed in `tickers.json` — same file the existing toolkit uses. Users can add/remove tickers at any time.

Rules in skill:
- Read `strategy/PAPER.md` + `experience/INDEX.md` before every decision
- Only 120+ DTE options
- Can use up to 100% of settled cash
- Never trade on high IV
- Mean reversion: buy puts on soaring stocks, calls on dipping stocks
- Check news — don't trade against fundamentally justified moves
- Sandbox phase: lean toward trading more to build experiences
- Max 5 open positions total across all tickers (prevents runaway accumulation)
- Never buy a duplicate position (same ticker, type, strike, expiry)

**`skills/paper-trade-status/SKILL.md`** — Interactive. Triggers: "paper trading status", "how are your trades doing", "portfolio status". Runs `paper_trading.py status`.

**`skills/paper-trade-history/SKILL.md`** — Interactive. Triggers: "paper trade history", "recent trades", "trade log". Runs `paper_trading.py history`.

### Step 5: Update Workspace Files

**`AGENTS.md`** — Add paper trading section:
- 3 new skills in the table
- Note about autonomous evaluation cron
- `paper_trading.py` as a tool Eva can use
- **Update Safety section** — add write permissions for:
  - `experience/` — Eva creates and edits experience files (theses, evidence, INDEX.md)
  - `strategy/PAPER.md` — Eva can make small, evidence-backed refinements and add Testing entries
  - `data/paper-trading/` — populated by `paper_trading.py` commands (reasons.json, known_positions.json, log.jsonl) — Eva does NOT write to these directly, only through CLI commands
- **Explicit restriction:** `reset` command is NOT allowed autonomously — only when a user directly tells Eva to reset

**`TOOLS.md`** — Add paper_trading.py commands + Tradier config reference

**`HEARTBEAT.md`** — Add: check paper trading positions, flag large P&L moves, weekly portfolio summary

### Step 6: Set Up OpenClaw Cron

```bash
openclaw cron add \
  --name "paper-trade-eval" \
  --cron "*/15 9-15 * * 1-5" \
  --tz "America/New_York" \
  --message "Run paper trading evaluation cycle. Use the paper-trade-evaluate skill." \
  --channel discord \
  --to <paper-trading-channel-id> \
  --announce
```

Mon-Fri 9:00-15:59 ET. Python script guards for 9:30 start.

**Prerequisite:** Create a `paper-trading` Discord channel and get its ID before setting up the cron. Channel ID goes in the cron config above.

### Step 7: Create Paper Strategy

**File:** `~/.openclaw/workspace/strategy/PAPER.md`

```markdown
# Paper Trading Strategy

## Purpose

Learn and build experiences. Trade frequently. Losses are data.

## Core Approach: Mean Reversion with News Filter

Buy options betting that extreme moves will reverse — unless there's a
fundamental reason they won't.

## Rules

### Entry Criteria
1. **Only trade 120+ DTE options.** Never buy weeklies or short-dated.
2. **Stock is soaring → buy a put.** Expect a pullback.
3. **Stock is dipping → buy a call.** Expect a recovery.
4. **Never trade on high IV.** If IV is elevated, options are too
   expensive — the mean reversion needs to be larger to profit.
5. **News filter:** Before trading against a move, analyze the news.
   If there's a fundamental reason the move should continue (earnings
   blowout, major acquisition, regulatory action), do NOT trade against it.
   Only trade when the move looks like overreaction or momentum without substance.

### Position Limits
- Max 5 open positions at a time.
- Can only use **settled cash** — unsettled funds from closed trades take 1 day to clear.
- Can use up to 100% of settled cash on a single trade.
- No minimum position size — even one contract is fine.
- No duplicate positions (same ticker, type, strike, expiry).

### Exit Criteria
- **Sell when the market is about to move against the position.** Target peaks — don't wait for full reversal to unwind.
- Compare current conditions to `entry_context` — has the underlying moved as expected? Has IV changed? Is the original thesis still valid?
- Cut losses if the thesis is clearly wrong (news changes, trend accelerates, entry_context shows conditions have fundamentally shifted).
- Re-evaluate every position each cycle — don't just hold and forget.
- Use judgment — no hard stop-loss percentages for now.

### Learning Priority
- **Trade more, not less.** The goal is to build experiences.
- Lean toward taking trades even when uncertain — paper exists to learn
  from mistakes.
- Every trade (win or loss) is valuable data for the experience system.
- Document reasoning thoroughly so experiences are rich.
- When a trade closes, ALWAYS reflect and update the relevant experience.

## Testing

User-suggested or Eva-proposed rule changes under evaluation.
Add entries here with the date and source. Promote to core rules or
remove based on paper trading results.

(none yet)
```

**Strategy is a living document.** Eva reads this before every evaluation cycle. Unlike experiences (which evolve frequently), strategy changes are rare and deliberate:

- **Eva-initiated:** As patterns emerge from the experience system, Eva can make small refinements — e.g., tightening entry criteria based on repeated losses. Changes should be conservative and evidence-backed.
- **User-initiated:** Users can suggest strategy tweaks (e.g., "try buying on earnings dips"). Eva adds these to a `## Testing` section in the strategy file, trades on them during paper trading, and either promotes them to core rules or removes them based on results.
- **Core rules stay stable.** The baseline rules (120+ DTE, mean reversion, news filter) don't change without strong evidence from multiple trades.

### Step 8: Update Documentation

**New:** `docs/paper-trading/overview.md`, `commands.md`, `experience-system.md`
**Updated:** `docs/README.md`, `docs/architecture/system-design.md`, skill docs

---

## Files Summary

**New files (~13):**
- `options-toolkit/paper_trading.py` (~500-600 lines)
- `options-toolkit/tradier.json` (config — user fills in token + account ID)
- `experience/README.md` (how the system works)
- `experience/INDEX.md` (empty index — Eva populates as she learns)
- `experience/general/` (empty dir — Eva creates files as she learns)
- `experience/tickers/` (empty dir — Eva creates per-ticker dirs as needed)
- `skills/paper-trade-evaluate/SKILL.md`
- `skills/paper-trade-status/SKILL.md`
- `skills/paper-trade-history/SKILL.md`
- `strategy/PAPER.md`
- `docs/paper-trading/overview.md`, `commands.md`, `experience-system.md`

**Modified files (5):**
- `AGENTS.md`, `TOOLS.md`, `HEARTBEAT.md`
- `docs/README.md`, `docs/architecture/system-design.md`

**NOT modified:** `toolkit.py`, `run_all.sh`, `tickers.json`, `news_research.py`

---

## Verification

1. Put sandbox token + account ID in `tradier.json` under `paper` key
2. `python3 paper_trading.py status` → shows Tradier sandbox account balance
3. `python3 paper_trading.py evaluate --ticker IWM --force` → outputs evaluation JSON
4. `python3 paper_trading.py buy --ticker IWM --type call --strike 265 --expiry 2026-06-30 --reason "test"` → places paper order via Tradier
5. `python3 paper_trading.py status` → shows position from Tradier
6. `python3 paper_trading.py sell --ticker IWM --type call --strike 265 --expiry 2026-06-30 --reason "test"` → closes position
7. `python3 paper_trading.py history` → shows orders from Tradier + local reasoning
8. `python3 paper_trading.py evaluate --ticker IWM --force` → `recently_closed` should show the closed position
9. Ask Eva "paper trading status" in Discord → triggers skill
