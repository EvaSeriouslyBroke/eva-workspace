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

**IV tracking:** Each evaluation saves an IV snapshot to `data/{mode}/{TICKER}/iv/{date}.json`. Over time this builds a history used to compute `iv_context` — IV rank (position in 52-week range), IV percentile (% of days IV was lower), and 52-week high/low.

**News tracking:** Each evaluation fetches fresh headlines from yfinance and saves a snapshot to `data/{mode}/{TICKER}/news/{date}.json` (appended each cycle). The 14-day history is included in evaluation output as `news_history`. Deep news research is done separately via the `news-research` command, only for tickers Eva wants to buy or double down on.

**Position snapshots:** Each cycle records price, IV, and Greeks for every open position belonging to the ticker (saved to `position-snapshots/{OCC}.jsonl`). When a position closes, its full snapshot history is included in `recently_closed` as `position_snapshots` alongside `entry_market_context`. Closed entries are deleted from `known_positions.json`. Open positions include a `snapshot_count` field indicating history depth.

**Local files read:** `known_positions.json`, `reasons.json`
**Local files written:** `known_positions.json` (reflected status, closed entry deletion), `pending_experience_updates.json` (closed position data for reflect skill), `position-snapshots/*.jsonl`

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

**API endpoints:** `POST /accounts/{id}/orders`

**Local files written:** `reasons.json`, `log.jsonl`, `pending_experience_updates.json`, `known_positions.json`

The sell command immediately writes the closed position (with entry context, snapshots, and reasoning) to `pending_experience_updates.json` and removes the entry from `known_positions.json`. This lets the next reflect cycle process the experience without waiting for `detect_recently_closed`.

**Discord:** Automatically sends a trade notification to the paper-trading channel.

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
4. Clear `reasons.json` and `known_positions.json`
