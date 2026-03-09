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
- Max 10 open positions at a time.
- Can only use **settled cash** — unsettled funds from closed trades take 1 day to clear.
- Can use up to 100% of settled cash on a single trade.
- No minimum position size — even one contract is fine.
- No duplicate positions (same ticker, type, strike, expiry).

### Doubling Down
- If an open position is moving against the thesis (e.g., bought a call and
  the stock keeps dipping), consider buying another contract at a better
  strike — the mean reversion thesis is now stronger if fundamentals haven't
  changed.
- Re-check the news filter before adding. If there's a fundamental reason the
  move should continue, do NOT double down — cut losses instead.
- IV must still not be elevated. A move against the thesis often spikes IV,
  making additional contracts expensive. Only add if IV is reasonable.
- Same position limits apply — the new position counts toward the 10-position
  max and must use settled cash.
- Use a different strike (closer to current price) so the new contract has
  better leverage on the expected reversal. Same expiry is fine.
- Max one double-down per ticker — don't layer three or four positions on the
  same thesis.

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
