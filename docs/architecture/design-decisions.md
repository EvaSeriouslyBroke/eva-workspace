# Design Decisions

Every non-obvious choice in the toolkit and why it was made. If you're wondering "why not just X?", check here first.

---

## Why yfinance

**Decision**: Use `yfinance` (unofficial Yahoo Finance wrapper) as the sole data source.

**Alternatives considered**:
- **Tradier** — Free sandbox tier, 60 req/min, 15-min delay, ORATS-quality IV. Good API but requires account signup and API key management.
- **Charles Schwab** — Free with brokerage account, 120 req/min, real-time. Requires OAuth flow, account setup.
- **Polygon.io** — Free tier limited for options data. Paid tiers expensive.
- **CBOE/Livevol** — Institutional-grade, paid. Overkill for this use case.

**Why yfinance wins**:
1. **Zero setup** — `pip install yfinance` and go. No API key, no account, no OAuth.
2. **IV per strike** — `impliedVolatility` field on every contract. Most free APIs don't provide this.
3. **Single-ticker use case** — We fetch one ticker at a time with gaps between. yfinance handles this fine.
4. **News included** — `Ticker.news` provides headlines without a separate API.
5. **Options chain** — `Ticker.option_chain(expiry)` returns calls and puts DataFrames with all needed columns.

**Known limitations**:
- Yahoo has tightened rate limits (429 errors possible with bulk requests). Our single-ticker-at-a-time pattern avoids this.
- Data is 15-minute delayed for some fields. Acceptable for options analysis (IV doesn't change dramatically minute-to-minute).
- Unofficial API — could break if Yahoo changes their backend. Risk accepted for simplicity.

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

**Storage math**: ~2KB per snapshot × 39 runs/day (every 10 min, 9:30-16:00 = 39 intervals) × 252 trading days/year = **~20MB/year per ticker**. Even with 10 tickers, that's 200MB/year. Negligible.

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

**Decision**: Store data as `data/{TICKER}/{YYYY}-W{WW}/{YYYY-MM-DD}.json` — one file per trading day, grouped in ISO 8601 week folders.

**Alternatives**:
- Single file per ticker — grows too large, slow to parse
- One file per run — too many files, filesystem clutter
- Monthly folders — too many days per folder, harder to find recent data
- Database (SQLite) — adds dependency, harder to inspect/debug

**Week/day grouping wins because**:
1. **Manageable file sizes** — Each daily file has ~39 entries (~78KB). Easy to open, inspect, edit.
2. **Natural browsing** — `ls data/IWM/` shows weeks. `ls data/IWM/2026-W08/` shows days. Intuitive.
3. **Easy comparison** — Finding "yesterday's data" is just looking at the previous day file in the same or adjacent week folder.
4. **Simple implementation** — `mkdir -p` for the week folder, JSON array append for the day file.
5. **No dependencies** — Just files and folders. No database driver.

---

## Why `--force` Flag

**Decision**: The `report` command silently exits (code 0, no output) outside market hours unless `--force` is passed.

**Two execution contexts**:
1. **Cron** — Fires broadly (9:00-16:50 ET) but toolkit self-filters to 9:30-16:00 ET. Outside those hours, cron runs should produce nothing. No output means `run_all.sh` skips sending to Discord. Clean.
2. **Interactive** — User asks "run the report for IWM" at 8 PM. They expect a report, not silence. `--force` bypasses the hours check.

**Why not just skip the hours check entirely**:
- Cron would send stale/after-hours data to Discord 78 times a day (every 10 min, 24/7) instead of 39 times
- After-hours option pricing is thin, spreads are wide, IV is unreliable

**Why not use a separate flag like `--cron`**:
- `--force` is a well-understood pattern ("override the safety check")
- Skills always pass `--force` — simple and obvious

---

## Why `---SPLIT---` Markers

**Decision**: The report output includes literal `---SPLIT---` lines at logical section boundaries. The caller (run_all.sh or Eva) splits on these markers.

**The problem**: Discord has a 2000-character message limit. Reports are ~4000-5000 characters. They need to be split into chunks.

**Alternative approaches**:
- Split at character count (e.g., every 1900 chars) — breaks mid-line, mid-table, mid-section. Ugly.
- Split at double-newlines — unpredictable chunk sizes, might still exceed 2000.
- Have the script send to Discord directly — couples the script to Discord, can't use stdout for other purposes.

**`---SPLIT---` markers win because**:
1. **Logical breaks** — Each chunk is a complete, coherent section (header+price+news, tables, summary+footer).
2. **Predictable** — Always 3 chunks at the same section boundaries.
3. **Target sizing** — Each chunk targets <1900 chars (100-char safety margin).
4. **Caller decides** — Script is a pure function (input → output). Whether output goes to Discord, a file, or stdout display is the caller's decision.
5. **Simple parsing** — `awk '/^---SPLIT---$/' { ... }` is trivial.

**3 chunks**:
1. History + Header + Price + News (Sections 1-4)
2. Expiry + Call Table + Put Table (Sections 5-7)
3. IV Summary + Footer + Save Confirmation (Section 8)

---

## Why stdout-Based Architecture

**Decision**: `toolkit.py` writes formatted output to stdout and errors to stderr. It never sends messages, writes to Discord, or does any delivery.

**Principle**: Scripts are pure functions — `(ticker, flags) → formatted text`. Delivery is the caller's responsibility.

**Benefits**:
1. **Testable** — Run the script, capture stdout, compare to expected output. No mocking Discord.
2. **Composable** — Pipe output wherever you want: Discord, file, terminal, email.
3. **Debuggable** — Run manually and see exactly what would be sent.
4. **Error separation** — Errors go to stderr, so a wrapper script won't accidentally send error messages to Discord.
5. **No credentials** — The script doesn't need Discord tokens or channel IDs.

**This means**:
- `run_all.sh` handles splitting and `openclaw message send` calls
- Eva's skill instructions handle splitting and posting
- The script itself is completely delivery-agnostic

---

## Why Not Handle NYSE Holidays

**Decision**: The market hours guard checks time-of-day and weekday but does NOT check for NYSE holidays (Good Friday, MLK Day, etc.).

**Why not**:
- Requires either hardcoding a holiday calendar (maintenance burden) or a package like `exchange_calendars` (extra dependency)
- Impact is low: on a holiday, the script runs but yfinance returns stale data or empty chains. The report either shows "no data" or shows yesterday's closing data — neither is harmful.
- Cron still only fires Mon-Fri, so only ~9 holidays/year are affected.

Impact is accepted — not a bug.

---

## Why a Separate Script for Deep News Research

**Decision**: Create `news_research.py` as a standalone script rather than adding a `deep-news` subcommand to `toolkit.py`.

**Alternatives considered**:
- **New subcommand in toolkit.py** — Adds `trafilatura` and `duckduckgo-search` as dependencies of the main CLI. Cron imports them even when running `report`. Risk of breakage.
- **Extend existing `news` command** — Adding `--deep` flag bloats a simple command. Different output format (JSON for AI synthesis vs formatted text for direct posting).

**Separate script wins because**:
1. **Isolation** — `toolkit.py` and cron pipeline are completely unaffected. New dependencies (`trafilatura`, `duckduckgo-search`) only load when `news_research.py` runs.
2. **Different output paradigm** — `toolkit.py news` outputs formatted text for direct posting. `news_research.py` outputs JSON for Eva to synthesize. Mixing these in one command would be awkward.
3. **Different use case** — Quick headlines (2s) vs deep analysis (8-10s). Different intents, different tools.
4. **Failure isolation** — If trafilatura breaks or DuckDuckGo rate-limits, it only affects deep research. Cron reports and quick headlines keep working.

**Trade-off**: Sentiment scoring logic is duplicated (not imported from toolkit.py). This is intentional — keeps both scripts fully independent. The algorithm is simple (~40 lines) and unlikely to diverge.

---

## Why Two News Skills Instead of One

**Decision**: Separate `stock-news` (quick headlines) and `stock-news-deep` (deep analysis) skills.

**Why not combine them**: Users have different intents. "IWM news" wants a fast answer (~2s). "Dig into IWM news" wants depth (~8-10s). A combined skill would either always be slow or need Eva to guess the intent — adding complexity to the skill description and body.

**Separate skills**:
1. **Clear triggers** — Eva knows exactly which tool to use based on the user's phrasing
2. **Predictable latency** — Quick news is always fast, deep news is always thorough
3. **Independent evolution** — Can improve deep analysis without touching the quick path
4. **Cost**: One more skill description in Eva's context (~100 words). Acceptable given the value.
