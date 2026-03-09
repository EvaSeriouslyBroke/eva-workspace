# HEARTBEAT.md

## During Market Hours (9:30-16:00 ET, Mon-Fri)

- Check paper trading positions: `python3 options-toolkit/eva.py status`
- Flag any positions with >20% P&L moves (up or down) — note in memory
- Check `options-toolkit/data/cron.log` for errors
- Note any unusual IV movements from recent report data

## End of Day (after 16:00 ET)

- Note any paper trades made today in `memory/YYYY-MM-DD.md`
- Summarize the day's IV trends to memory

## Weekly (Monday morning)

- Review `experience/INDEX.md` — any patterns becoming clearer?
- Paper trading summary: total P&L, win/loss ratio, experience updates
- Review `memory/` files from past week, clean up stale notes
