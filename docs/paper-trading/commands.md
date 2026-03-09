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
- `GET /markets/options/chains?symbol=X&expiration=DATE&greeks=true` — option chain

**Output:** Single ticker returns a JSON object; `--all` returns a JSON array. Each contains:
- `account` — cash, settled/unsettled, equity
- `positions` — open positions with entry_context
- `recently_closed` — positions closed since last eval
- `market.intraday` — today's open/high/low/last, change_pct, range_position (0=at low, 100=at high)
- `market.recent_days` — last 5 trading days with OHLC and daily change_pct (most recent first)
- `market.trends` — SMA 50/200, returns (1w/1m/3m/6m/1y), 52-week range, trend_summary
- `market.chain_summary` — near-money calls/puts with IV, delta, volume, P/C ratio
- `market.iv_context` — IV rank, IV percentile, 52-week IV high/low
- `affordable_options` — options within settled_cash budget

**IV tracking:** Each evaluation saves an IV snapshot to `data/{TICKER}/iv/{date}.json`. Over time this builds a history used to compute `iv_context` — IV rank (position in 52-week range), IV percentile (% of days IV was lower), and 52-week high/low.

**Local files read:** `known_positions.json`, `reasons.json`

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
python3 eva.py buy --ticker IWM --type call --strike 265 --expiry 2026-06-30 --quantity 1 --reason "Mean reversion — IWM dipped 3%"
```

**Flags:**
- `--ticker` (required) — ticker symbol
- `--type` (required) — `call` or `put`
- `--strike` (required) — strike price
- `--expiry` (required) — expiration date (YYYY-MM-DD)
- `--quantity` (default: 1) — number of contracts
- `--reason` (required) — trade reasoning

**Checks:** Duplicate position check before placing order.

**API endpoints:** `GET /markets/quotes` (entry context), `GET /markets/options/chains` (entry IV), `POST /accounts/{id}/orders`

**Local files written:** `reasons.json` (order ID → reasoning), `known_positions.json` (position tracker), `log.jsonl`

**Discord:** Automatically sends a trade notification to the paper-trading channel.

---

## `sell`

Place a sell_to_close market order.

```bash
python3 eva.py sell --ticker IWM --type call --strike 265 --expiry 2026-06-30 --quantity 1 --reason "Thesis played out — recovered 2%"
```

Same flags as `buy`.

**API endpoints:** `POST /accounts/{id}/orders`

**Local files written:** `reasons.json`, `log.jsonl`

**Discord:** Automatically sends a trade notification to the paper-trading channel.

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
