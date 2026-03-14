#!/usr/bin/env bash
# Dispatch hindsight analysis — one isolated agent session per closed watch.
# Called by system crontab on Fridays. Each symbol gets its own session
# to keep context small and space out API calls.
set -euo pipefail

export PATH="/home/henry/.npm-global/bin:/usr/local/bin:/usr/bin:$PATH"

DIR="$(cd "$(dirname "$0")" && pwd)"
CHANNEL="1479499260188950671"  # paper trading Discord channel

# Timezone guard — only run at 4 PM ET (handles DST via dual crontab entries)
CURRENT_HOUR=$(TZ=America/New_York date +%H)
if [ "$CURRENT_HOUR" != "16" ]; then
  exit 0
fi

# Get symbols needing analysis
SYMBOLS=$(python3 "$DIR/eva.py" hindsight --list 2>/dev/null \
  | python3 -c "import sys,json; [print(s['symbol']) for s in json.load(sys.stdin)]" 2>/dev/null) || exit 0

if [ -z "$SYMBOLS" ]; then
  exit 0
fi

# Trigger an isolated agent session for each symbol
for SYM in $SYMBOLS; do
  openclaw agent \
    --agent main \
    -m "Run hindsight analysis for $SYM. Use the paper-trade-hindsight skill." \
    --deliver \
    --channel discord \
    --reply-to "$CHANNEL" \
    || echo "Failed to dispatch hindsight for $SYM" >&2
  sleep 30
done

# Clean up expired and stale watches after all analyses are dispatched
python3 "$DIR/eva.py" hindsight --clear-expired
