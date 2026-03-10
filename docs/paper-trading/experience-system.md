# Experience System

Eva's thesis-based learning system. The canonical reference for file format, required tags, confidence levels, evolution rules, and evidence management is **`experience/README.md`**. This doc covers only how the experience system integrates with paper trading.

## Integration with Paper Trading

### Writing Experiences

- **From trades:** The `sell` command immediately writes closed position data to `pending_experience_updates.json` (with entry context, snapshots, and reasoning). For expirations, `detect_recently_closed` in the evaluate cycle handles detection. The `paper-trade-reflect` skill (running ~7 min after each evaluate cycle) reads this file, creates/updates experience files, then clears the pending file. Evidence entries include date, mode tag (`[paper]`/`[real]`), and description.
- **From hindsight:** After selling, the contract continues to be tracked until expiration (post-sale snapshots recorded every evaluate cycle). The `paper-trade-hindsight` skill (weekly) analyzes what actually happened — was the sell well-timed? What patterns were missed? Evidence entries use the `[hindsight]` tag and focus on sell timing, counterfactual outcomes, and luck-vs-skill assessment.
- **From observations:** Eva can create experience files from patterns noticed in `news_history` and `market_history` data (14 days each) without having traded. For example, noticing that tariff news consistently precedes a 2-day IWM dip. These observational experiences use the same file format but note `[observed]` in evidence entries.

### Recalling Experiences

Eva recalls experiences **after** forming a tentative decision, not before. This prevents anchoring bias — she assesses the market fresh, then checks memory.

The recall flow:
1. Eva makes a tentative decision based on strategy rules + market data
2. For each planned action (buy/sell/double down), Eva spawns a subagent to search experiences
3. The subagent reads INDEX.md, finds matching experiences by ticker AND by pattern tags across all tickers/general
4. Eva reviews the findings and confirms, adjusts, or reverses her decision
5. Experience findings are included in the trade's `--reason`

This mirrors human memory — assess the situation first, then think "have I seen this before?"

## Who Writes Experiences

Eva writes experiences through the LLM (not code) because categorization, analysis, and thesis refinement require judgment. The `experience/` directory is outside AGENTS.md restricted paths.
