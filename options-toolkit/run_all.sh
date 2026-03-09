#!/usr/bin/env bash
set -euo pipefail

export PATH="/home/henry/.npm-global/bin:/usr/local/bin:/usr/bin:$PATH"

DIR="$(cd "$(dirname "$0")" && pwd)"

TICKERS=$(python3 -c "import json; d=json.load(open('$DIR/tickers.json')); print(' '.join(d['tickers']))")
CHANNEL=$(python3 -c "import json; d=json.load(open('$DIR/tickers.json')); print(d['discord_channel'])")

send_chunks() {
  local output="$1"
  local channel="$2"
  echo "$output" | awk -v ch="$channel" '
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
}

for TICKER in $TICKERS; do
  # Regular report
  OUTPUT=$(python3 "$DIR/eva.py" report --ticker "$TICKER" 2>/dev/null) || true
  if [ -n "$OUTPUT" ]; then
    send_chunks "$OUTPUT" "$CHANNEL"
    sleep 2
  fi

  # End-of-day summary
  SUMMARY=$(python3 "$DIR/eva.py" summary --ticker "$TICKER" 2>/dev/null) || true
  if [ -n "$SUMMARY" ]; then
    send_chunks "$SUMMARY" "$CHANNEL"
    sleep 2
  fi
done
