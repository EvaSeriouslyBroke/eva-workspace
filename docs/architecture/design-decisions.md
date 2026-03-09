# Design Decisions

Every non-obvious choice in the toolkit and why it was made. If you're wondering "why not just X?", check here first.

---

## Why Tradier API

**Decision**: Use Tradier API as the primary market data and trading API, with DuckDuckGo for news.

**Alternatives considered**:
- **yfinance** — Original choice. Zero setup, but unofficial API that could break, no trading capability, and Yahoo tightened rate limits. Replaced during the unified refactor.
- **Charles Schwab** — Free with brokerage account, 120 req/min, real-time. Requires OAuth flow, account setup.
- **Polygon.io** — Free tier limited for options data. Paid tiers expensive.
- **CBOE/Livevol** — Institutional-grade, paid. Overkill for this use case.

**Why Tradier wins**:
1. **Unified data + trading** — Single API for market data, options chains with greeks, AND order execution. No need for separate data and trading providers.
2. **IV per strike with full greeks** — `mid_iv`, `smv_vol`, delta, gamma, theta, vega, rho, and open_interest on every contract.
3. **Paper trading sandbox** — Free sandbox environment with identical API surface. Test strategies without risk.
4. **Real-time data** — No 15-minute delay on quotes (sandbox has delays but live is real-time).
5. **Clean REST API** — Well-documented, simple authentication, predictable responses.

**For news**: DuckDuckGo via the `duckduckgo-search` library — no API key needed, free, returns headlines with URLs for deep extraction via trafilatura.

---

## Why System Crontab Over OpenClaw Cron

**Decision**: Use the OS-level `crontab` instead of OpenClaw's built-in cron system.

**OpenClaw cron** (`openclaw cron add|list|rm|run`):
- Triggers an LLM agent conversation for each job execution
- Agent receives the job prompt, reasons about it, and runs commands
- Designed for tasks that need AI judgment

**The problem**: Our scheduled reports are purely mechanical. The same command runs every time. No judgment needed. Running through the LLM:
- Burns tokens (cost) for zero added value
- Adds latency (agent reasoning time)
- Introduces non-determinism (agent might behave differently)
- Could fail if agent context is confused

**System cron**:
- Runs shell commands directly — zero overhead
- Deterministic — same input, same output, every time
- Free — no token cost
- Fast — no agent startup time

**Trade-off**: We lose OpenClaw's job management UI (`openclaw cron list`). Worth it for a mechanical task.

---

## Why 5 Skills Instead of 1

**Decision**: Create separate skills for `price`, `chain`, `news`, `history`, and `report` instead of a single "options analyzer" skill.

**Single skill approach**: Eva would need to parse the user's intent ("do they want just the price? the full report? just news?") from the skill body instructions. Complexity in the skill body, harder to maintain.

**Five skills approach**:
1. **Modularity** — Each skill does one thing. Easy to understand, test, maintain.
2. **Specific triggers** — "what's IWM at?" triggers `stock-price`, not the full report. User gets a fast answer.
3. **Independent evolution** — Can update the news skill without touching the report skill.
4. **Smaller skill bodies** — Each skill body is 25-35 lines. Eva loads less context.
5. **Natural conversation** — User can ask follow-up questions that trigger different skills ("now show me the chain", "any news?").

**Cost**: 5 skill descriptions are always in Eva's context instead of 1. Each description is ~100 words, so ~500 words total. Acceptable — skill descriptions are designed for this.

---

## Why Data Grows Forever

**Decision**: Never delete historical data files. Let them accumulate indefinitely.

**Storage math**: ~2KB per snapshot × 6 runs/day (6 scheduled report times) × 252 trading days/year = **~3MB/year per ticker**. Even with 10 tickers, that's 30MB/year. Negligible.

**Benefits of keeping everything**:
1. **Trend analysis** — Can look at IV trends over weeks, months, quarters
2. **Historical context** — "What was IV like last earnings season?"
3. **Pattern recognition** — Compare current conditions to similar past conditions
4. **No recovery needed** — Can't accidentally lose data that you need later
5. **Future features** — Charting, backtesting, ML training all need historical data

**Why not cap/rotate**:
- Adds complexity (rotation logic, deciding what's "old enough" to delete)
- Saves negligible disk space
- Removes optionality (can't un-delete data)

---

## Why Week/Day File Grouping

**Decision**: Store data as `data/{mode}/{TICKER}/{YYYY}-W{WW}/{YYYY-MM-DD}.json` — one file per trading day, grouped in ISO 8601 week folders, separated by mode.

**Alternatives**:
- Single file per ticker — grows too large, slow to parse
- One file per run — too many files, filesystem clutter
- Monthly folders — too many days per folder, harder to find recent data
- Database (SQLite) — adds dependency, harder to inspect/debug

**Week/day grouping wins because**:
1. **Manageable file sizes** — Each daily file has ~6 entries (~12KB). Easy to open, inspect, edit.
2. **Natural browsing** — `ls data/paper/IWM/` shows weeks. `ls data/paper/IWM/2026-W08/` shows days. Intuitive.
3. **Easy comparison** — Finding "yesterday's data" is just looking at the previous day file in the same or adjacent week folder.
4. **Simple implementation** — `mkdir -p` for the week folder, JSON array append for the day file.
5. **No dependencies** — Just files and folders. No database driver.

---

## Why `--force` Flag

**Decision**: The `report` command silently exits (code 0, no output) outside scheduled times unless `--force` is passed.

**Two execution contexts**:
1. **Cron** — Fires at both EST and EDT UTC equivalents, but the Python guard only allows fires that match the SCHEDULE. Outside those times, cron runs should produce nothing. No output means `run_all.sh` skips sending to Discord. Clean.
2. **Interactive** — User asks "run the report for IWM" at 8 PM. They expect a report, not silence. `--force` bypasses the schedule check.

**Why not just skip the schedule check entirely**:
- Cron would send reports at wrong-season UTC fires (13 fires/day instead of 6-7 producing output)
- After-hours option pricing is thin, spreads are wide, IV is unreliable

**Why not use a separate flag like `--cron`**:
- `--force` is a well-understood pattern ("override the safety check")
- Skills always pass `--force` — simple and obvious

---

## Why `---SPLIT---` Markers

**Decision**: The report output includes literal `---SPLIT---` lines at logical section boundaries. The caller (run_all.sh or Eva) splits on these markers.

**The problem**: Discord has a 2000-character message limit. Reports are ~3000-4000 characters. They need to be split into chunks.

**Alternative approaches**:
- Split at character count (e.g., every 1900 chars) — breaks mid-line, mid-table, mid-section. Ugly.
- Split at double-newlines — unpredictable chunk sizes, might still exceed 2000.
- Have the script send to Discord directly — couples the script to Discord, can't use stdout for other purposes.

**`---SPLIT---` markers win because**:
1. **Logical breaks** — Each chunk is a complete, coherent section.
2. **Predictable** — Always 3 chunks at the same section boundaries.
3. **Target sizing** — Each chunk targets <1900 chars (100-char safety margin).
4. **Caller decides** — Script is a pure function (input → output). Whether output goes to Discord, a file, or stdout display is the caller's decision.
5. **Simple parsing** — `awk '/^---SPLIT---$/' { ... }` is trivial.

**3 chunks**:
1. History + Header + Price
2. Call Table + Put Table
3. IV Summary + Footer + Save Confirmation

---

## Why stdout-Based Architecture

**Decision**: `eva.py` writes formatted output to stdout and errors to stderr. Market data commands (`price`, `chain`, `news`, `history`, `report`, `summary`) are pure stdout — they never send messages or do delivery. The caller handles delivery.

**Exception**: The `buy` and `sell` commands also send trade notification messages to the paper-trading Discord channel via `openclaw message send`. This is intentional — trade notifications are part of the command's action, not a delivery concern.

**Principle**: Market data commands are pure functions — `(ticker, flags) → formatted text`. Delivery is the caller's responsibility.

**Benefits**:
1. **Testable** — Run the script, capture stdout, compare to expected output. No mocking Discord.
2. **Composable** — Pipe output wherever you want: Discord, file, terminal, email.
3. **Debuggable** — Run manually and see exactly what would be sent.
4. **Error separation** — Errors go to stderr, so a wrapper script won't accidentally send error messages to Discord.
5. **No credentials** — The script doesn't need Discord tokens or channel IDs.

**This means** (for market data commands):
- `run_all.sh` handles splitting and `openclaw message send` calls
- Eva's skill instructions handle splitting and posting
- Market data commands are completely delivery-agnostic

---

## Why Not Handle NYSE Holidays

**Decision**: The schedule guard checks time-of-day and weekday but does NOT check for NYSE holidays (Good Friday, MLK Day, etc.).

**Why not**:
- Requires either hardcoding a holiday calendar (maintenance burden) or a package like `exchange_calendars` (extra dependency)
- Impact is low: on a holiday, the script runs but Tradier returns stale data or the market is closed. The report either shows stale data or produces empty chains — neither is harmful.
- Cron still only fires Mon-Fri, so only ~9 holidays/year are affected.

Impact is accepted — not a bug.

---

## Why a Separate Subcommand for Deep News Research

**Decision**: Implement deep news research as the `news-research` subcommand of `eva.py`, with lazy imports for its heavy dependencies.

**Why a separate subcommand** (not merged into `news`):
1. **Different output paradigm** — `eva.py news` outputs formatted text for direct posting. `eva.py news-research` outputs JSON for Eva to synthesize. Different intents, different outputs.
2. **Different use case** — Quick headlines (2s) vs deep analysis (8-10s). Different intents, different tools.
3. **Lazy imports** — `trafilatura` is only imported when `news-research` runs. Other subcommands and cron are unaffected.
4. **Failure isolation** — If trafilatura breaks or DuckDuckGo rate-limits, it only affects deep research. Cron reports and quick headlines keep working.

---

## Why Two News Skills Instead of One

**Decision**: Separate `stock-news` (quick headlines) and `stock-news-deep` (deep analysis) skills.

**Why not combine them**: Users have different intents. "IWM news" wants a fast answer (~2s). "Dig into IWM news" wants depth (~8-10s). A combined skill would either always be slow or need Eva to guess the intent — adding complexity to the skill description and body.

**Separate skills**:
1. **Clear triggers** — Eva knows exactly which tool to use based on the user's phrasing
2. **Predictable latency** — Quick news is always fast, deep news is always thorough
3. **Independent evolution** — Can improve deep analysis without touching the quick path
4. **Cost**: One more skill description in Eva's context (~100 words). Acceptable given the value.
