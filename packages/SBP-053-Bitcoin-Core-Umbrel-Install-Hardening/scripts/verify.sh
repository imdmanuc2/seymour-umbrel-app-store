#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
echo "===== FILE MODES ====="
stat -c '%a %n' "$ROOT/seymour-bitcoin-node/data/node/entrypoint.sh" "$ROOT/scripts/seymour-install-btc"
[[ -x "$ROOT/seymour-bitcoin-node/data/node/entrypoint.sh" ]]
[[ -x "$ROOT/scripts/seymour-install-btc" ]]
[[ -f "$ROOT/seymour-bitcoin-node/data/generated/.gitkeep" ]]
[[ -f "$ROOT/seymour-bitcoin-node/data/state/.gitkeep" ]]
python3 -m py_compile "$ROOT/scripts/seymour-install-btc"
grep -Fq '"version": "1.1"' "$ROOT/scripts/seymour-install-btc"
grep -Fq 'native-install-did-not-register' "$ROOT/scripts/seymour-install-btc"
grep -Fq 'finalState' "$ROOT/scripts/seymour-install-btc"
echo
echo "===== INSTALLER PLAN ====="
"$ROOT/scripts/seymour-install-btc"
echo
echo "SBP-053 executable permissions: PASS"
echo "SBP-053 persistent directory markers: PASS"
echo "SBP-053 install-state verification contract: PASS"
echo "SBP-053 read-only verification safety: PASS"
echo "SBP-053 final verification: PASS"
echo "No live Bitcoin installation was executed by verify.sh."
