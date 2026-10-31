#!/usr/bin/env bash
# Live licence demo for judges, one step per Enter key. Run from the repo root on the vendor laptop.
#
#   scripts/demo_licence.sh                      # live server, 5-minute licence
#   MIN=2 scripts/demo_licence.sh                # shorter wait
#   B=http://127.0.0.1:8000 scripts/demo_licence.sh
#
# Always ends by uploading the long licence, so the server is never left locked.
set -euo pipefail
B=${B:-https://scammap-huii.onrender.com}
MIN=${MIN:-5}
LONG=licences/demo-bank-long.json
NUMBER=9845011111
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

step() { printf '\n\033[1;33m== %s\033[0m\n' "$1"; read -r -p "   (Enter) "; }
show() { printf '\033[2m$ %s\033[0m\n' "$*"; "$@"; echo; }
renew() { curl -s -X POST "$B/license" -H 'content-type: application/json' -d @"$LONG" >/dev/null || true; }

step "0. Wake the server"
show curl -s "$B/health"

step "1. The app works, and GET /license shows who it is licensed to and until when"
show curl -s "$B/license"
show curl -s "$B/lookup?type=phone&value=$NUMBER"

step "2. A forged licence is refused (one date changed, signature no longer matches)"
python3 - "$LONG" "$TMP/forged.json" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1])); d["expires_at"] = "2099-01-01T00:00:00+05:30"; json.dump(d, open(sys.argv[2], "w"))
EOF
show curl -s -X POST "$B/license" -H 'content-type: application/json' -d @"$TMP/forged.json"

step "3. Mint a ${MIN}-minute licence here on the vendor laptop and upload it"
trap 'renew; rm -rf "$TMP"' EXIT INT
show uv run python -m scripts.mint_licence --licensee "Demo Bank (${MIN} min)" --minutes "$MIN" --out "$TMP/short.json"
show curl -s -X POST "$B/license" -H 'content-type: application/json' -d @"$TMP/short.json"
show curl -s "$B/lookup?type=phone&value=$NUMBER"

step "4. Wait for it to expire (open the app on a phone now)"
while :; do
  left=$(curl -s "$B/license" | python3 -c 'import sys, json; print(json.load(sys.stdin)["seconds_remaining"])')
  printf '\r   seconds remaining: %-6s' "$left"
  [ "$left" -le 0 ] && break
  sleep 5
done
sleep 6  # the active licence is cached for at most 5 seconds
echo
show curl -s -w '  HTTP %{http_code}' "$B/lookup?type=phone&value=$NUMBER"
show curl -s -w '  HTTP %{http_code}' "$B/health"
show curl -s "$B/license"
echo "   On the phone: look the number up again to see the 'Licence expired' screen."

step "5. Renew with the long licence: works at once, no restart, data intact"
show curl -s -X POST "$B/license" -H 'content-type: application/json' -d @"$LONG"
show curl -s "$B/lookup?type=phone&value=$NUMBER"
trap 'rm -rf "$TMP"' EXIT
echo "   On the phone: tap 'Try again'."
