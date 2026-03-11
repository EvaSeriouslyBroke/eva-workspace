# Paper Trading Commands

All commands are subcommands of `eva.py`. Global flag: `--mode paper|real` (default: paper).

---

## `evaluate`

Build evaluation JSON for Eva to reason about a ticker.

```bash
python3 eva.py evaluate --ticker IWM [--force]
python3 eva.py evaluate --all [--force]
```

**Flags:**
- `--ticker` — ticker symbol (or use `--all`)
- `--all` — evaluate all tickers from `trading_tickers.json` in one invocation (fetches account/positions/orders once, then per-ticker market data)
- `--force` — bypass market hours check

**Market hours check:** Before fetching any data, calls `GET /markets/clock` to check if the market is open. Silently exits (code 0) if the market is closed (weekends, holidays, half days). `--force` skips this check.

**API endpoints used:**
- `GET /markets/clock` — market open/closed check
- `GET /accounts/{id}/balances` — cash, equity
- `GET /accounts/{id}/positions` — open positions
- `GET /accounts/{id}/orders` — for closed-trade detection
- `GET /markets/quotes?symbols=X` — current price
- `GET /markets/history?symbol=X` — daily price history (1 year)
- `GET /markets/options/expirations?symbol=X` — available expirations
- `GET /markets/options/chains?symbol=X&expiration=DATE&greeks=true` — option chain with all Greeks
- yfinance news — fetches fresh headlines every evaluate cycle per ticker

**Output:** Single ticker returns a JSON object; `--all` returns a JSON array. Each contains:
- `account` — cash, settled/unsettled, equity
- `positions` — open positions with entry_context
- `recently_closed` — positions closed since last eval
- `market.intraday` — today's open/high/low/last, change_pct, range_position (0=at low, 100=at high)
- `market.recent_days` — last 5 trading days with OHLC and daily change_pct (most recent first)
- `market.market_history` — 14 days of price, IV, and Greeks data
- `market.trends` — SMA 50/200, returns (1w/1m/3m/6m/1y), 52-week range, trend_summary
- `market.chain_summary` — near-money calls/puts with all Greeks (IV, delta, gamma, theta, vega, rho, open_interest), volume, P/C ratio
- `market.iv_context` — IV rank, IV percentile, 52-week IV high/low
- `market.news` — current headlines with sentiment scores
- `market.news_history` — 14-day news sentiment history from saved snapshots
- `available_expirations` — all option expirations with DTE, so Eva can see short-term options too
- `affordable_options` — options within settled_cash budget, with all Greeks (delta, gamma, theta, vega, rho, open_interest)

**IV tracking:** Each evaluation saves a market snapshot to `data/{mode}/{TICKER}/snapshots/{date}.json` with expanded data (intraday, trends, IV context, sentiment, broader market). Over time this builds a history used to compute `iv_context` — IV rank (position in 52-week range), IV percentile (% of days IV was lower), and 52-week high/low. The legacy `iv/` directory is still read as a fallback when no `snapshots/` data exists.

**News tracking:** Each evaluation fetches fresh headlines from yfinance and saves a snapshot to `data/{mode}/{TICKER}/news/{date}.json` (appended each cycle). The 14-day history is included in evaluation output as `news_history`. Deep news research is done separately via the `news-research` command, only for tickers Eva wants to buy or double down on.

**Position snapshots:** Each cycle records price, IV, and Greeks for every open position belonging to the ticker (saved to `position-snapshots/{OCC}.jsonl`). When a position closes, its full snapshot history is included in `recently_closed` as `position_snapshots` alongside `entry_market_context`. Closed entries are deleted from `known_positions.json`. Open positions include a `snapshot_count` field indicating history depth.

**Post-sale snapshots:** Each cycle also records price, IV, and Greeks for sold contracts still being watched (saved to `post-sale-snapshots/{OCC}.jsonl`). Watches are loaded from `closed_watches.json`; only non-expired contracts are tracked. The evaluation output includes a `closed_watches` array summarizing all watched contracts for the ticker.

**Local files read:** `known_positions.json`, `reasons.json`, `closed_watches.json`
**Local files written:** `known_positions.json` (reflected status, closed entry deletion), `pending_experience_updates.json` (closed position data for reflect skill), `position-snapshots/*.jsonl`, `post-sale-snapshots/*.jsonl`

---

## `status`

Formatted portfolio status for Discord.

```bash
python3 eva.py status
```

**API endpoints:** balances, positions, orders

**Output:** Pre-formatted text with emoji dividers — post as-is to Discord.

---

## `buy`

Place a buy_to_open market order.

```bash
python3 eva.py buy --ticker IWM --type call --strike 265 --expiry 2026-06-30 --quantity 1 --reason "IWM dipped 3% with elevated IV — expecting bounce"
```

**Flags:**
- `--ticker` (required) — ticker symbol
- `--type` (required) — `call` or `put`
- `--strike` (required) — strike price
- `--expiry` (required) — expiration date (YYYY-MM-DD)
- `--quantity` (default: 1) — number of contracts
- `--reason` (required) — trade reasoning

**API endpoints:** `GET /markets/quotes` (entry context), `GET /markets/options/chains` (full Greeks), `GET /markets/history` (price trends), `POST /accounts/{id}/orders`

**Market context captured at buy time:** The buy command captures rich market context including all option Greeks (IV, delta, gamma, theta, vega, rho), IV rank/percentile, price trends (SMA 50/200, 52-week position), and news headlines. This context is stored in both `reasons.json` and `known_positions.json` so it's available during later evaluation and experience reflection.

**Local files written:** `reasons.json` (order ID → reasoning + market_context), `known_positions.json` (position tracker + market_context), `log.jsonl`

**Discord:** Automatically sends a trade notification to the paper-trading channel.

---

## `sell`

Place a sell_to_close market order.

```bash
python3 eva.py sell --ticker IWM --type call --strike 265 --expiry 2026-06-30 --quantity 1 --reason "Thesis played out — recovered 2%"
```

Same flags as `buy`.

**API endpoints:** `GET /markets/quotes` (sell context), `GET /markets/options/chains` (sell-time Greeks/IV), `POST /accounts/{id}/orders`

**Market context captured at sell time:** The sell command captures the option's bid price, IV, and Greeks at the moment of sale. This sell-time context is stored in `closed_watches.json` alongside entry context, enabling hindsight comparison.

**Local files written:** `reasons.json`, `log.jsonl`, `pending_experience_updates.json`, `known_positions.json`, `closed_watches.json`

The sell command immediately writes the closed position (with entry context, snapshots, and reasoning) to `pending_experience_updates.json` and removes the entry from `known_positions.json`. It also adds the contract to `closed_watches.json` for post-sale tracking until expiration.

**Discord:** Automatically sends a trade notification to the paper-trading channel.

---

## `hindsight`

Post-sale hindsight analysis for closed watches.

```bash
python3 eva.py hindsight
python3 eva.py hindsight --symbol IWM260517C00250000
python3 eva.py hindsight --expired-only
python3 eva.py hindsight --clear-expired
```

**Flags:**
- `--symbol` — specific OCC symbol to analyze
- `--expired-only` — only show expired contracts with complete lifecycle data
- `--clear-expired` — remove expired contracts from watch list after analysis

**Output:** JSON with per-contract analysis including:
- `realized_pnl` / `realized_pnl_pct` — what Eva actually made/lost
- `counterfactual.hold_to_now_value` — what the position would be worth now (or at expiry)
- `counterfactual.peak_value_after_sale` / `peak_date` — best possible exit after sale
- `counterfactual.trough_value_after_sale` / `trough_date` — worst point after sale
- `counterfactual.missed_upside` — how much more she could have made
- `counterfactual.avoided_downside` — how much loss the sell prevented
- `counterfactual.sell_was_optimal` — did the sell beat holding to now?
- `daily_trajectory` — day-by-day post-sale summaries (option bid OHLC, IV, delta, theta, underlying price, DTE)
- `key_moments` — full snapshots at `first_after_sell`, `at_peak`, `at_trough`, `latest` (all Greeks, IV, prices)
- `news_around_key_dates` — headlines from days around sell date, peak date, trough date (+/- 1 day)
- `market_around_key_dates` — stock price and IV data on those same dates
- `entry_market_context` / `sell_market_context` — market conditions at entry and exit
- `open_reason` / `close_reason` — Eva's reasoning at entry and exit

**Local files read:** `closed_watches.json`, `position-snapshots/*.jsonl` (pre-sale), `post-sale-snapshots/*.jsonl`, `data/{mode}/{TICKER}/news/*.json`, `data/{mode}/{TICKER}/iv/*.json`
**Local files written:** `closed_watches.json` (when `--clear-expired`), deletes `post-sale-snapshots/{OCC}.jsonl` for cleared symbols

---

## `pending-experience`

Show or clear pending experience updates from closed positions.

```bash
python3 eva.py pending-experience
python3 eva.py pending-experience --clear
```

**Flags:**
- `--clear` — delete the pending file after processing

**Output:** JSON array of closed position records (same format as `recently_closed`). Empty array (`[]`) if nothing pending.

**Local files read:** `pending_experience_updates.json`
**Local files written:** `pending_experience_updates.json` (deleted when `--clear`)

---

## `trade-history`

Show order history merged with local reasoning.

```bash
python3 eva.py trade-history [--limit 20]
```

**Flags:**
- `--limit` (default: 20) — max orders to show

**API endpoints:** `GET /accounts/{id}/orders`

**Local files read:** `reasons.json`

---

## `reset`

Cancel all orders, close all positions, archive local data. **User-only — never autonomous.**

```bash
python3 eva.py reset --confirm
```

**Flags:**
- `--confirm` (required) — safety gate

**Actions:**
1. Archive `reasons.json` to `reasons.YYYY-MM-DD.json`
2. Cancel all open/pending orders via `DELETE /accounts/{id}/orders/{oid}`
3. Close all positions via `POST /accounts/{id}/orders` (sell_to_close)
4. Clear `reasons.json`, `known_positions.json`, `closed_watches.json`, and `pending_experience_updates.json`
5. Delete `position-snapshots/` and `post-sale-snapshots/` directories
