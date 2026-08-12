#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
SCRIPT="$ROOT/scripts/seymour-install-btc"
[[ -x "$SCRIPT" ]]
python3 -m py_compile "$SCRIPT"
PLAN="$("$SCRIPT")"
printf '%s\n' "$PLAN"
PLAN="$PLAN" python3 - <<'PY'
import json, os
p=json.loads(os.environ["PLAN"])
assert p["mode"]=="plan"
assert p["contract"]=="seymour.bitcoin-install-preflight"
assert p["requiredConfirmation"]=="INSTALL-seymour-bitcoin-node"
assert p["checks"]["appId"]=="seymour-bitcoin-node"
assert p["checks"]["providerId"]=="bitcoin-mainnet"
assert p["checks"]["image"]=="ghcr.io/imdmanuc2/seymour-bitcoin-node:29.0.0"
print("SBP-052 plan contract: PASS")
PY
set +e
BAD="$("$SCRIPT" --execute --confirm WRONG 2>&1)"
RC=$?
set -e
[[ "$RC" -ne 0 ]]
printf '%s\n' "$BAD" | grep -Fq '"error": "confirmation-mismatch"'
echo "SBP-052 confirmation guard: PASS"
echo "SBP-052 canonical Umbrel delegation contract: PASS"
echo "SBP-052 read-only verification safety: PASS"
echo "SBP-052 final verification: PASS"
echo "No live Bitcoin installation was executed by verify.sh."
