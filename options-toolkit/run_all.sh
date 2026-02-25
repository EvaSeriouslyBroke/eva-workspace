#!/usr/bin/env bash
set -euo pipefail

export PATH="/home/henry/.npm-global/bin:/usr/local/bin:/usr/bin:$PATH"

DIR="$(cd "$(dirname "$0")" && pwd)"

TICKERS=$(python3 -c "import json; d=json.load(open('$DIR/tickers.json')); print(' '.join(d['tickers']))")
CHANNEL=$(python3 -c "import json; d=json.load(open('$DIR/tickers.json')); print(d['discord_channel'])")

for TICKER in $TICKERS; do
  OUTPUT=$(python3 "$DIR/toolkit.py" report --ticker "$TICKER" 2>/dev/null) || true

  [ -z "$OUTPUT" ] && continue

  echo "$OUTPUT" | awk -v ch="$CHANNEL" '
    BEGIN { buf="" }
    /^---SPLIT---$/ {
      if (buf != "") {
        cmd = "openclaw message send --channel discord --target " ch " --message \047" buf "\047"
        system(cmd)
        system("sleep 1")
      }
      buf=""
      next
    }
    { buf = buf (buf=="" ? "" : "\n") $0 }
    END {
      if (buf != "") {
        cmd = "openclaw message send --channel discord --target " ch " --message \047" buf "\047"
        system(cmd)
      }
    }
  '

  sleep 2
done
